import random
import aiohttp
from loguru import logger
from bs4 import BeautifulSoup

from creart import create
from graia.ariadne.message.chain import MessageChain

from shared.models.config import GlobalConfig

config = create(GlobalConfig)
proxy = config.proxy if config.proxy != "proxy" else ""


async def get_weibo_trending() -> MessageChain:
    weibo_hot_url = "https://api.weibo.cn/2/guest/search/hot/word"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=weibo_hot_url) as resp:
            data = await resp.json()
    data = data["data"]
    text_list = [f"随机数:{random.randint(0, 10000)}", "\n微博实时热榜:"]
    for index, i in enumerate(data, start=1):
        text_list.append(f"\n{index}. {i['word'].strip()}")
    text = "".join(text_list).replace("#", "")
    return MessageChain(text)


async def get_zhihu_trending() -> MessageChain:
    zhihu_hot_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=zhihu_hot_url) as resp:
            data = await resp.json()
    data = data["data"]
    text_list = [f"随机数:{random.randint(0, 10000)}", "\n知乎实时热榜:"]
    for index, i in enumerate(data, start=1):
        text_list.append(f"\n{index}. {i['target']['title'].strip()}")
    text = "".join(text_list).replace("#", "")
    print(text)
    return MessageChain(text)


async def get_github_trending() -> MessageChain:
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/87.0.4280.141 Safari/537.36 "
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers, proxy=proxy) as resp:
            html = await resp.read()
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", {"class": "Box-row"})

    text_list = [f"随机数:{random.randint(0, 10000)}", "\ngithub实时热榜:\n"]
    index = 0
    for i in articles:
        try:
            index += 1
            title = (
                i.find("h1")
                .get_text()
                .replace("\n", "")
                .replace(" ", "")
                .replace("\\", " \\ ")
            )
            text_list.append(f"\n{index}. {title}\n")
            text_list.append(f"\n    {i.find('p').get_text().strip()}\n")
        except Exception as e:
            logger.error(e)

    text = "".join(text_list).replace("#", "")
    return MessageChain(text)
