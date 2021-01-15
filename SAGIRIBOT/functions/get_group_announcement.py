import base64

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import App


async def get_group_announcement(content: str) -> list:
    group_announcement_json = """
                {
                    "app": "com.tencent.mannounce",
                    "config": {
                        "ctime": 1610424762,
                        "forward": 0,
                        "token": "190bcca54b1eb9c543676aa1c82762ab"
                    },
                    "desc": "群公告",
                    "extra": {
                        "app_type": 1,
                        "appid": 1101236949,
                        "uin": 1900384123
                    },
                    "meta": {
                        "mannounce": {
                            "cr": 1,
                            "encode": 1,
                            "fid": "93206d3900000000ba21fd5fa58a0500",
                            "gc": "963453075",
                            "sign": "cbbf90a7cbf1dc938ac5bdb8224fc3cb",
                            "text": "%s",
                            "title": "576k5YWs5ZGK",
                            "tw": 1,
                            "uin": "1900384123"
                        }
                    },
                    "prompt": "[群公告]test",
                    "ver": "1.0.0.43",
                    "view": "main"
                }""" % base64.b64encode(content.encode('utf-8'))
    return [
        "None",
        MessageChain.create([
            App(content=group_announcement_json)
        ])
    ]