import aiohttp
import random

from graia.application.message.elements.internal import Plain
from graia.application.message.chain import MessageChain


async def get_weibo_hot() -> list:
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
    return [
        "None",
        MessageChain.create([
            Plain(text=text)
        ])
    ]