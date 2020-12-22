import aiohttp
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.tools import text2piiic
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting


async def get_jlu_csw_notice(group_id: int) -> list:
    """
    Get JLU CSW notice

    Args:
        group_id: Group id

    Examples:
        msg = await get_jlu_csw_notice()

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    url = "https://api.sagiri-web.com/JLUCSWNotice/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            res = await resp.json()

    data = res["data"]
    content = "----------------------------------\n"
    for i in range(10):
        content += f"{data[i]['title']}\n"
        content += f"{data[i]['href']}\n"
        content += f"                                        {data[i]['time'].replace('-', '.')}\n"
        content += "----------------------------------\n"

    long_text_setting = await get_setting(group_id, "longTextType")
    if long_text_setting == "img":
        img = text2piiic(string=content, poster="", length=max(len(x) for x in content.split("\n")))
        img.save("./statics/temp/tempJLUCSWNotice.png")
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile("./statics/temp/tempJLUCSWNotice.png")
            ])
        ]
    elif long_text_setting == "text":
        return [
            "None",
            MessageChain.create([
                Plain(text=content)
            ])
        ]
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="数据库 longTextType 项出错！请检查！")
            ])
        ]

