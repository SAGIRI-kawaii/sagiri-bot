import random
import aiohttp
from bs4 import BeautifulSoup

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.MessageSender.Strategy import Normal
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount


class TrendingHandler(AbstractHandler):
    """
    热搜Handler
    """
    __name__ = "TrendingHandler"
    __description__ = "一个获取热搜的Handler"
    __usage__ = "在群中发送 `微博热搜` 即可查看微博热搜\n在群中发送 `知乎热搜` 即可查看知乎热搜\n在群中发送 `github热搜` 即可查看github热搜"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text == "微博热搜":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_weibo_trending(group, member))
        elif message_text == "知乎热搜":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_zhihu_trending(group, member))
        elif message_text == "github热搜":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_github_trending(group, member))
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
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal(GroupStrategy()))

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
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal(GroupStrategy()))

    @staticmethod
    @frequency_limit_require_weight_free(1)
    async def get_github_trending(group: Group, member: Member) -> MessageItem:
        url = "https://github.com/trending"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as resp:
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
            except Exception:
                pass

        text = "".join(text_list).replace("#", "")
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal(GroupStrategy()))
