# import base64
# import ujson as json

# from graia.amnesia.message.chain import MessageChain
# from avilla.core.elements import Text, Picture, Audio, Notice


# async def message_chain_to_json(message: MessageChain) -> str:
#     """
#     对 MessageChain 进行 Json 序列化
#     """
#     result = []
#     for element in message.__root__:
#         if isinstance(element, Text):
#             result.append({"type": "Text", "text": element.text})
#         elif isinstance(element, Picture):
#             result.append({
#                 "type": "Picture",
#                 "id": element.id,
#                 "url": element.url,
#                 "base64": base64.b64encode(await element.get_bytes()).decode(
#                     "utf-8"
#                 ),
#             })
#         elif isinstance(element, Face):
#             result.append(
#                 {"type": "Face", "face_id": element.face_id, "name": element.name}
#             )
#         elif isinstance(element, Audio):
#             result.append({
#                     "type": "Audio",
#                     "id": element.id,
#                     "url": element.url,
#                     "base64": base64.b64encode(await element.get_bytes()).decode(
#                         "utf-8"
#                     ),
#                     "length": element.length,
#             })
#         elif isinstance(element, Notice):
#             result.append(
#                 {"type": "Notice", "target": dict(element.target), "display": str(element)}
#             )
#     return json.dumps(result)


# def json_to_message_chain(data: str | dict | list) -> MessageChain:
#     if isinstance(data, str):
#         data = json.loads(data)
#     elements = []
#     for i in data:
#         if i["type"] == "Text":
#             elements.append(Text(i["text"]))
#         elif i["type"] == "Picture":
#             elements.append(Picture(base64=i["base64"]))
#         elif i["type"] == "Face":
#             elements.append(Face(i["face_id"]))
#         elif i["type"] == "Notice":
#             elements.append(Notice(target=i["target"]))
#     return MessageChain(elements)


# def parse_message_chain_as_stable_string(message: MessageChain) -> str:
#     copied_msg = message.copy()
#     return copied_msg.as_persistent_string(binary=False)
