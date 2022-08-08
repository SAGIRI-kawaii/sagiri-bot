import json
import base64
from typing import Union

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Face, Voice, At


async def message_chain_to_json(message: MessageChain) -> str:
    """
    对 MessageChain 进行 Json 序列化
    """
    result = []
    for element in message.__root__:
        if isinstance(element, Plain):
            result.append({"type": "Plain", "text": element.text})
        elif isinstance(element, Image):
            result.append(
                {
                    "type": "Image",
                    "id": element.id,
                    "url": element.url,
                    "base64": base64.b64encode(await element.get_bytes()).decode(
                        "utf-8"
                    ),
                }
            )
        elif isinstance(element, Face):
            result.append(
                {"type": "Face", "face_id": element.face_id, "name": element.name}
            )
        elif isinstance(element, Voice):
            result.append(
                {
                    "type": "Voice",
                    "id": element.id,
                    "url": element.url,
                    "base64": base64.b64encode(await element.get_bytes()).decode(
                        "utf-8"
                    ),
                    "length": element.length,
                }
            )
        elif isinstance(element, At):
            result.append(
                {"type": "At", "target": element.target, "display": element.display}
            )
    return json.dumps(result)


def json_to_message_chain(data: Union[str, dict, list]) -> MessageChain:
    if isinstance(data, str):
        data = json.loads(data)
    elements = []
    for i in data:
        if i["type"] == "Plain":
            elements.append(Plain(i["text"]))
        elif i["type"] == "Image":
            elements.append(Image(base64=i["base64"]))
        elif i["type"] == "Face":
            elements.append(Face(i["face_id"]))
        elif i["type"] == "At":
            elements.append(At(target=i["target"]))
    return MessageChain(elements)
