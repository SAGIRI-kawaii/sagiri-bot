import aiohttp
import random

from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.chain import MessageChain

from SAGIRIBOT.basics.tools import text2piiic
from SAGIRIBOT.basics.tools import count_len
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting


async def get_zhihu_hot(group_id: int) -> list:
    zhihu_hot_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=zhihu_hot_url) as resp:
            data = await resp.json()
    print(data)
    data = data["data"]
    text_list = [f"随机数:{random.randint(0,10000)}", "\n知乎实时热榜:"]
    index = 0
    for i in data:
        index += 1
        text_list.append("\n%d. %s" % (index, i["target"]["title"]))
    text = "".join(text_list).replace("#", "")
    long_text_setting = await get_setting(group_id, "longTextType")
    if long_text_setting == "img":
        img = text2piiic(string=text, poster="", length=int(max(count_len(line) for line in text.split("\n")) / 2))
        img.save("./statics/temp/tempZhihu.png")
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile("./statics/temp/tempZhihu.png")
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
