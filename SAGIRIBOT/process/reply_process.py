import aiohttp

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At

from SAGIRIBOT.data_manage.get_data.get_setting import get_setting
from SAGIRIBOT.functions.get_chat_reply import get_chat_reply
from SAGIRIBOT.basics.get_config import get_config


async def reply_process(group_id: int, sender: int, message_text: str) -> list:
    """
    Auto reply process

    Args:
        group_id: Group id
        sender: Sender
        message_text: Message text

    Examples:
        massage = await reply_process(12345678, 12345678, "你好")

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    mode_now = await get_setting(group_id, "speakMode")
    text = ""
    if mode_now == "normal":
        pass
    elif mode_now == "chat":
        text = await get_chat_reply(group_id, sender, message_text)
        if text == "":
            text = "我不知道怎么回答呐~抱歉哦~"
    elif mode_now == "zuanLow":
        url = "https://nmsl.shadiao.app/api.php?level=min&from=%s" % await get_config("shadiaoAppName")
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                text = await resp.text()
    elif mode_now == "zuanHigh":
        url = "https://nmsl.shadiao.app/api.php?from=%s" % await get_config("shadiaoAppName")
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                text = await resp.text()
    elif mode_now == "rainbow":
        url = "https://chp.shadiao.app/api.php?from=%s" % await get_config("shadiaoAppName")
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                text = await resp.text()
    return [
        "None",
        MessageChain.create([
            At(sender),
            Plain(text=text)
        ])
    ]