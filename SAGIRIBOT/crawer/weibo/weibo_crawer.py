import aiohttp
import random

from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.chain import MessageChain

from SAGIRIBOT.basics.tools import text2piiic
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting


async def get_weibo_hot(group_id: int) -> list:
    weibo_hot_url = "http://api.weibo.cn/2/guest/search/hot/word"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=weibo_hot_url) as resp:
            data = await resp.json()
    data = data["data"]
    text_list = [f"随机数:{random.randint(0,10000)}", "\n微博实时热榜:"]
    index = 0
    for i in data:
        index += 1
        text_list.append("\n%d.%s" % (index, i["word"]))
    text = "".join(text_list).replace("#", "")
    long_text_setting = await get_setting(group_id, "longTextType")
    if long_text_setting == "img":
        img = text2piiic(string=text, poster="", length=max(len(x) for x in text.split("\n")))
        img.save("./statics/temp/tempWeibo.png")
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile("./statics/temp/tempWeibo.png")
            ])
        ]
    elif long_text_setting == "text":
        return [
            "None",
            MessageChain.create([
                Plain(text=text)
            ])
        ]
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="数据库 longTextType 项出错！请检查！")
            ])
        ]
