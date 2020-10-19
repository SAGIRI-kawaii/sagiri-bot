import re
import time
import random
import string
import aiohttp
from urllib.parse import quote

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At

from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.basics.tools import get_tx_sign
from SAGIRIBOT.basics.tools import curl_md5


async def text_detect(text: str) -> str:
    """
    Detect the language

    Args:
        text: Text to be detected

    Examples:
        source = text_detect(text)

    Return:
        str
    """
    url = "https://api.ai.qq.com/fcgi-bin/nlp/nlp_textdetect"

    t = time.time()
    time_stamp = str(int(t))

    nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 10))

    app_id = await get_config("txAppId")
    params = {
        'app_id': app_id,
        'candidate_langs': '',
        'force': '1',
        'nonce_str': nonce_str,
        'text': text,
        'time_stamp': time_stamp
    }
    sign = await get_tx_sign(params)
    params['sign'] = sign

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as resp:
            res = await resp.json()
    # print(res)
    return res["data"]["lang"]


async def get_translate(message_text: str, sender: int) -> list:
    """
    Translate the text

    Args:
        message_text: Message text
        sender: Sender

    Examples:
        message = await get_translate(message_text, sender)

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    # print(message_text)
    support_language = {"中文": "zh", "英文": "en", "日文": "jp", "韩文": "kr", "法文": "fr", "西班牙文": "es", "意大利文": "it",
                       "德文": "de", "土耳其文": "tr", "俄文": "ru", "葡萄牙文": "pt", "越南文": "vi", "印度尼西亚文": "id",
                       "马来西亚文": "ms", "泰文": "th"}
    tp = re.findall(r' (.*?)用(.*?)怎么说', message_text, re.S)[0]
    text = tp[0]
    target = tp[1]
    source = await text_detect(text)

    if target not in support_language.keys():
        all_support_language = "、".join(support_language.keys())
        return [
            "None",
            MessageChain.create([
                At(target=sender),
                Plain(text="目前只支持翻译到%s哦~\n要全字匹配哦~看看有没有打错呐~\n翻译格式：text用（目标语言）怎么说" % all_support_language)
            ])
        ]

    target = support_language[target]
    # print(target)
    url = "https://api.ai.qq.com/fcgi-bin/nlp/nlp_texttranslate"
    t = time.time()
    time_stamp = str(int(t))
    nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 10))
    app_id = await get_config("txAppId")
    app_key = await get_config("txAppKey")
    params = {
        'app_id': app_id,
        'text': text,
        'time_stamp': time_stamp,
        'nonce_str': nonce_str,
        'source': source,
        'target': target
    }
    params["sign"] = await get_tx_sign(params)

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as resp:
            res = await resp.json()

    print("翻译（%s -> %s）：%s" % (source, target, text))

    return [
        "None",
        MessageChain.create([
            At(target=sender),
            Plain("translate:\n"),
            Plain(text="%s" % res["data"]["target_text"])
        ])
    ]