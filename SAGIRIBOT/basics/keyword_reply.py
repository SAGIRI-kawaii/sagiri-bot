import json

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Plain


async def keyword_reply(message_text: str):
    with open('./json/reply_keywords.json', 'r', encoding='utf-8') as f:  # 从json读配置
        keywords_dict = json.loads(f.read())
    if message_text in keywords_dict.keys():
        return [
            "None",
            MessageChain.create([
                Plain(text=keywords_dict[message_text][1])
            ])
        ] if keywords_dict[message_text][0] == "text" else [
            "None",
            MessageChain.create([
                Image.fromLocalFile(keywords_dict[message_text][1])
            ])
        ]
    else:
        return None
