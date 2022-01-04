import random
import aiohttp
from bs4 import BeautifulSoup

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount


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


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def trending(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await Trending.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class Trending(AbstractHandler):
    """
    热搜Handler
    """
    __name__ = "Trending"
    __description__ = "一个获取热搜的插件"
    __usage__ = "在群中发送 `微博热搜` 即可查看微博热搜\n在群中发送 `知乎热搜` 即可查看知乎热搜\n在群中发送 `github热搜` 即可查看github热搜"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text == "微博热搜":
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            return await Trending.get_weibo_trending(group, member)
        elif message_text == "知乎热搜":
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            return await Trending.get_zhihu_trending(group, member)
        elif message_text == "github热搜":
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            return await Trending.get_github_trending(group, member)
        else:
            return None

    @staticmethod
    @frequency_limit_require_weight_free(1)
    async def get_weibo_trending(group: Group, member: Member) -> MessageItem:
        weibo_hot_url = "http://api.weibo.cn/2/guest/search/hot/word"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=weibo_hot_url) as resp:
                data = await resp.json()
        data = data["data"]
        text_list = [f"随机数:{random.randint(0, 10000)}", "\n微博实时热榜:"]
        index = 0
        for i in data:
            index += 1
            text_list.append(f"\n{index}. {i['word'].strip()}")
        text = "".join(text_list).replace("#", "")
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal())

    @staticmethod
    @frequency_limit_require_weight_free(1)
    async def get_zhihu_trending(group: Group, member: Member) -> MessageItem:
        zhihu_hot_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=zhihu_hot_url) as resp:
                data = await resp.json()
        data = data["data"]
        text_list = [f"随机数:{random.randint(0, 10000)}", "\n知乎实时热榜:"]
        index = 0
        for i in data:
            index += 1
            text_list.append(f"\n{index}. {i['target']['title'].strip()}")
        text = "".join(text_list).replace("#", "")
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal())

    @staticmethod
    @frequency_limit_require_weight_free(1)
    async def get_github_trending(group: Group, member: Member) -> MessageItem:
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
                title = i.find('h1').get_text().replace('\n', '').replace(' ', '').replace('\\', ' \\ ')
                text_list.append(f"\n{index}. {title}\n")
                text_list.append(f"\n    {i.find('p').get_text().strip()}\n")
            except:
                pass

        text = "".join(text_list).replace("#", "")
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal())
