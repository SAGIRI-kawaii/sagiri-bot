import random
from bs4 import BeautifulSoup

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import UnionMatch, RegexResult

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()

channel.name("Trending")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个获取热搜的插件\n"
    "在群中发送 `微博热搜` 即可查看微博热搜\n"
    "在群中发送 `知乎热搜` 即可查看知乎热搜\n"
    "在群中发送 `github热搜` 即可查看github热搜"
)

core = AppCore.get_core_instance()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ''


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([UnionMatch("微博热搜", "知乎热搜", "github热搜") @ "trending_type"])],
        decorators=[
            FrequencyLimit.require("trending", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def trending(app: Ariadne, group: Group, trending_type: RegexResult):
    trending_type = trending_type.result.asDisplay()
    if trending_type == "微博热搜":
        await app.sendGroupMessage(group, await Trending.get_weibo_trending())
    elif trending_type == "知乎热搜":
        await app.sendGroupMessage(group, await Trending.get_zhihu_trending())
    elif trending_type == "github热搜":
        await app.sendGroupMessage(group, await Trending.get_github_trending())


class Trending(object):

    @staticmethod
    async def get_weibo_trending() -> MessageChain:
        weibo_hot_url = "http://api.weibo.cn/2/guest/search/hot/word"
        async with get_running(Adapter).session.get(url=weibo_hot_url) as resp:
            data = await resp.json()
        data = data["data"]
        text_list = [f"随机数:{random.randint(0, 10000)}", "\n微博实时热榜:"]
        for index, i in enumerate(data, start=1):
            text_list.append(f"\n{index}. {i['word'].strip()}")
        text = "".join(text_list).replace("#", "")
        return MessageChain(text)

    @staticmethod
    async def get_zhihu_trending() -> MessageChain:
        zhihu_hot_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
        async with get_running(Adapter).session.get(url=zhihu_hot_url) as resp:
            data = await resp.json()
        data = data["data"]
        text_list = [f"随机数:{random.randint(0, 10000)}", "\n知乎实时热榜:"]
        for index, i in enumerate(data, start=1):
            text_list.append(f"\n{index}. {i['target']['title'].strip()}")
        text = "".join(text_list).replace("#", "")
        return MessageChain(text)

    @staticmethod
    async def get_github_trending() -> MessageChain:
        url = "https://github.com/trending"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.141 Safari/537.36 "
        }
        async with get_running(Adapter).session.get(url=url, headers=headers, proxy=proxy) as resp:
            html = await resp.read()
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("article", {"class": "Box-row"})

        text_list = [f"随机数:{random.randint(0, 10000)}", "\ngithub实时热榜:\n"]
        index = 0
        for i in articles:
            try:
                index += 1
                title = i.find('h1').get_text().replace('\n', '').replace(' ', '').replace('\\', ' \\ ')
                text_list.append(f"\n{index}. {title}\n")
                text_list.append(f"\n    {i.find('p').get_text().strip()}\n")
            except:
                pass

        text = "".join(text_list).replace("#", "")
        return MessageChain(text)
