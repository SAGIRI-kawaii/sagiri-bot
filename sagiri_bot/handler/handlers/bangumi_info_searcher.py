import aiohttp
import urllib.parse as parse

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.utils import MessageChainUtils
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount
from sagiri_bot.decorators import frequency_limit_require_weight_free, switch, blacklist


saya = Saya.current()
channel = Channel.current()

channel.name("BangumiInfoSearcher")
channel.author("SAGIRI-kawaii")
channel.description("一个可以搜索番剧信息的插件，在群中发送 `番剧 {番剧名}` 即可")

proxy = AppCore.get_core_instance().get_config().proxy


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def bangumi_info_searcher(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await BangumiInfoSearcher.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class BangumiInfoSearcher(AbstractHandler):
    __name__ = "BangumiInfoSearcher"
    __description__ = "一个可以搜索番剧信息的插件"
    __usage__ = "在群中发送 `番剧 番剧名` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("番剧 "):
            await update_user_call_count_plus(group, member, UserCalledCount.search, "search")
            return await BangumiInfoSearcher.get_bangumi_info(group, member, message.asDisplay()[3:])
        else:
            return None

    @staticmethod
    @frequency_limit_require_weight_free(3)
    async def get_bangumi_info(group: Group, member: Member, keyword: str) -> MessageItem:
        headers = {
            "user-agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/84.0.4147.135 Safari/537.36 "
        }
        url = "https://api.bgm.tv/search/subject/%s?type=2&responseGroup=Large&max_results=1" % parse.quote(keyword)
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers) as resp:
                data = await resp.json()

        if "code" in data.keys() and data["code"] == 404 or not data["list"]:
            return MessageItem(MessageChain.create([Plain(text=f"番剧 {keyword} 未搜索到结果！")]), QuoteSource())

        bangumi_id = data["list"][0]["id"]
        url = "https://api.bgm.tv/subject/%s?responseGroup=medium" % bangumi_id

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, proxy=proxy if proxy != "proxy" else '') as resp:
                data = await resp.json()

        name = data["name"]
        cn_name = data["name_cn"]
        summary = data["summary"]
        img_url = data["images"]["large"]
        score = data["rating"]["score"]
        rank = data["rank"] if "rank" in data.keys() else None
        rating_total = data["rating"]["total"]

        async with aiohttp.ClientSession() as session:
            async with session.get(url=img_url, proxy=proxy if proxy != "proxy" else '') as resp:
                img_content = await resp.read()

        message = MessageChain.create([
            Plain(text="查询到以下信息：\n"),
            Image(data_bytes=img_content),
            Plain(text=f"名字:{name}\n\n中文名字:{cn_name}\n\n"),
            Plain(text=f"简介:{summary}\n\n"),
            Plain(text=f"bangumi评分:{score}(参与评分{rating_total}人)"),
            Plain(text=f"\n\nbangumi排名:{rank}" if rank else "")
        ])
        return MessageItem(
            await MessageChainUtils.messagechain_to_img(message=message, max_width=1080, img_fixed=True),
            QuoteSource()
        )
