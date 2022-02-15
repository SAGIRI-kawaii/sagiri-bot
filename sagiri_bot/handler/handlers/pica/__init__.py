import os
import aiohttp
from loguru import logger
from datetime import datetime, timedelta

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import UploadMethod
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.element import ForwardNode, Image, Plain, Forward
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, UnionMatch, ArgumentMatch

from .Pica import pica
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.utils import MessageChainUtils
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from utils.daily_number_limiter import DailyNumberLimiter
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import Normal, QuoteSource
from sagiri_bot.decorators import frequency_limit_require_weight_free

saya = Saya.current()
channel = Channel.current()

channel.name("Pica")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个接入哔咔漫画的插件，支持搜索关键词，随机漫画，下载漫画，排行榜获取\n"
    "在群中发送 `pica search {keyword}` 来搜索特定关键词\n"
    "在群中发送 `pica random` 来获取随机漫画\n"
    "在群中发送 `pica rank -H24/-D7/-D30` 来获取24小时/一周/一月内排行榜\n"
    "在群中发送 `pica download (-message|-forward) {comic_id}` 来获取图片消息/转发消息/压缩文件形式的漫画"
)

core = AppCore.get_core_instance()
config = core.get_config()
bot_qq = config.bot_qq
DOWNLOAD_CACHE = config.functions["pica"]["download_cache"]
SEARCH_CACHE = config.functions["pica"]["search_cache"]

BASE_PATH = os.path.dirname(__file__)
SEARCH_CACHE_PATH = BASE_PATH + "/cache/search"

if not os.path.exists(SEARCH_CACHE_PATH):
    os.makedirs(SEARCH_CACHE_PATH)

DAILY_DOWNLOAD_LIMIT = int(config.functions["pica"]["daily_download_limit"])
DAILY_SEARCH_LIMIT = int(config.functions["pica"]["daily_search_limit"])
DAILY_RANDOM_LIMIT = int(config.functions["pica"]["daily_random_limit"])
DAILY_RANK_LIMIT = int(config.functions["pica"]["daily_rank_limit"])

DAILY_DOWNLOAD_LIMITER = DailyNumberLimiter(DAILY_DOWNLOAD_LIMIT)
DAILY_SEARCH_LIMITER = DailyNumberLimiter(DAILY_SEARCH_LIMIT)
DAILY_RANDOM_LIMITER = DailyNumberLimiter(DAILY_RANDOM_LIMIT)
DAILY_RANK_LIMITER = DailyNumberLimiter(DAILY_RANK_LIMIT)

limit_text = {
    "download": "今天已经达到每日下载上限啦~\n明天再来吧~\n❤你❤这❤个❤小❤色❤批❤~",
    "search": "今天已经达到每日搜索上限啦~\n明天再来吧~\n想找本子的话，自己去下载个哔咔好咯~",
    "random": "今天已经达到每日随机本子上限啦~\n明天再来吧~\n你这个人对本子真是挑剔呢~",
    "rank": "今天已经达到每日排行榜查询上限啦~\n明天再来吧~\n排行榜一次还看不够嘛~"
}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [FullMatch("pica")],
                    {
                        "operation": UnionMatch("download", "search", "random", "rank", "init"),
                        "forward_type": ArgumentMatch("-forward", action="store_true", optional=True),
                        "message_type": ArgumentMatch("-message", action="store_true", optional=True),
                        "rank_time": UnionMatch("-H24", "-D7", "-D30", optional=True),
                        "content": RegexMatch(r".+", optional=True)
                    }
                )
            )
        ]
    )
)
async def pica_function(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    operation: UnionMatch,
    message_type: ArgumentMatch,
    forward_type: ArgumentMatch,
    rank_time: UnionMatch,
    content: RegexMatch
):
    if result := await PicaHandler.handle(
        app, message, group, member, operation, message_type, forward_type, rank_time, content
    ):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class PicaHandler(AbstractHandler):
    __name__ = "PicaHandler"
    __description__ = "一个接入哔咔漫画的插件，支持搜索关键词，随机漫画，下载漫画，排行榜获取"
    __usage__ = "在群中发送 `pica search {keyword}` 来搜索特定关键词\n" \
                "在群中发送 `pica random` 来获取随机漫画\n" \
                "在群中发送 `pica rank -H24/-D7/-D30` 来获取24小时/一周/一月内排行榜\n" \
                "在群中发送 `pica download (-message|-forward) {comic_id}` 来获取图片消息/转发消息/压缩文件形式的漫画"

    @staticmethod
    @switch()
    @blacklist()
    @frequency_limit_require_weight_free(9)
    async def handle(
        app: Ariadne,
        message: MessageChain,
        group: Group,
        member: Member,
        operation: UnionMatch,
        message_type: ArgumentMatch,
        forward_type: ArgumentMatch,
        rank_time: UnionMatch,
        content: RegexMatch
    ):
        if not pica.init:
            return MessageItem(MessageChain.create([Plain(text="pica实例初始化失败，请重启机器人或重载插件！")]), Normal())
        if any([
            operation.result.asDisplay() == "download" and not DAILY_DOWNLOAD_LIMITER.check(member.id),
            operation.result.asDisplay() == "search" and not DAILY_SEARCH_LIMITER.check(member.id),
            operation.result.asDisplay() == "random" and not DAILY_RANDOM_LIMITER.check(member.id),
            operation.result.asDisplay() == "rank" and not DAILY_RANK_LIMITER.check(member.id)
        ]):
            return MessageItem(
                MessageChain(limit_text[str(operation.result.asDisplay())]), QuoteSource()
            )

        if operation.result.asDisplay() == "download":
            DAILY_DOWNLOAD_LIMITER.increase(member.id)
        elif operation.result.asDisplay() == "search":
            DAILY_SEARCH_LIMITER.increase(member.id)
        elif operation.result.asDisplay() == "random":
            DAILY_RANDOM_LIMITER.increase(member.id)
        elif operation.result.asDisplay() == "rank":
            DAILY_RANK_LIMITER.increase(member.id)

        if operation.result.asDisplay() == "init":
            if pica.init:
                return MessageItem(MessageChain.create([Plain(text="pica已初始化")]), Normal())
            try:
                await pica.check()
                return MessageItem(MessageChain.create([Plain(text="pica初始化成功")]), Normal())
            except aiohttp.ClientConnectorError:
                return MessageItem(MessageChain.create([Plain(text="pica初始化失败，请检查代理")]), Normal())
        elif operation.result.asDisplay() == "download" and forward_type.matched and content.matched:
            comic_id = content.result.asDisplay()
            await app.sendMessage(group, MessageChain(f"收到请求，正在下载{comic_id}..."))
            info = await pica.download_comic(comic_id, False)
            image_list = []
            for root, _, files in os.walk(info[0]):
                for file in files:
                    if file[-4:] in (".jpg", ".png"):
                        image_list.append(os.path.join(root, file))
            node_count = 0
            time_count = 0
            time_base = datetime.now() - timedelta(seconds=len(image_list))
            forward_nodes = [ForwardNode(
                senderId=bot_qq,
                time=time_base + timedelta(seconds=time_count),
                senderName="纱雾酱",
                messageChain=MessageChain.create(Plain("IOS系统可能会乱序，请参照下方文件名和发送时间顺序自行排序！"))
            )]
            for path in image_list:
                node_count += 1
                time_count += 1
                forward_nodes.append(
                    ForwardNode(
                        senderId=bot_qq,
                        time=time_base + timedelta(seconds=time_count),
                        senderName="纱雾酱",
                        messageChain=MessageChain.create(
                            Image(path=path),
                            Plain(f"\n{path.replace(info[0], '')}\n{time_base + timedelta(seconds=time_count)}")
                        )
                    )
                )
                if node_count == 20:
                    await app.sendMessage(group, MessageChain.create(Forward(nodeList=forward_nodes)))
                    forward_nodes = [
                        ForwardNode(
                            senderId=bot_qq,
                            time=time_base + timedelta(seconds=time_count),
                            senderName="纱雾酱",
                            messageChain=MessageChain.create(Plain("IOS系统可能会乱序，请参照下方文件名和发送时间顺序自行排序！"))
                        )
                    ]
                    node_count = 0
            return MessageItem(MessageChain.create(Forward(nodeList=forward_nodes)), Normal())

        elif operation.result.asDisplay() == "download" and message_type.matched and content.matched:
            comic_id = content.result.asDisplay()
            await app.sendMessage(group, MessageChain(f"收到请求，正在下载{comic_id}..."))
            info = await pica.download_comic(comic_id, False)
            image_list = []
            for root, _, files in os.walk(info[0]):
                for file in files:
                    if not file[-3:] == "zip":
                        image_list.append(os.path.join(root, file))
            return MessageItem(MessageChain.create([Image(path=path) for path in image_list]), Normal())

        elif operation.result.asDisplay() == "download" and content.matched:
            comic_id = message.asDisplay()[14:]
            await app.sendMessage(group, MessageChain(f"收到请求，正在下载{comic_id}..."))
            info = await pica.download_comic(comic_id)
            try:
                await app.uploadFile(
                    data=info[1],
                    method=UploadMethod.Group,
                    target=group,
                    name=f"{info[0].replace(' ', '')}"
                )
            except RemoteException:
                await app.uploadFile(
                    data=info[1],
                    method=UploadMethod.Group,
                    target=group,
                    name=f"pica_{comic_id}"
                )
            return MessageItem(MessageChain("请自行添加 .zip 后缀名后进行解压"), Normal())

        elif operation.result.asDisplay() in ("search", "random"):
            search = operation.result.asDisplay() == "search"
            keyword = content.result.asDisplay() if content.matched else ''
            if search and content.matched:
                await app.sendMessage(group, MessageChain(f"收到请求，正在搜索{keyword}..."))
            data = (await pica.search(keyword))[:10] \
                if search else (await pica.random())[:10]
            forward_nodes = []
            for comic in data:
                comic_info = await pica.comic_info(comic["id"]) if operation.result.asDisplay() == "search" else comic
                try:
                    forward_nodes.append(
                        ForwardNode(
                            senderId=bot_qq,
                            time=datetime.now(),
                            senderName="纱雾酱",
                            messageChain=(await MessageChainUtils.messagechain_to_img(
                                MessageChain.create([
                                    await PicaHandler.get_thumb(comic_info),
                                    Plain(text=f"\n名称：{comic_info['title']}\n"),
                                    Plain(text=f"作者：{comic_info['author']}\n"),
                                    Plain(text=f"描述：{comic_info['description']}\n") if search else Plain(text=''),
                                    Plain(text=f"分类：{'、'.join(comic_info['categories'])}\n"),
                                    Plain(text=f"标签：{'、'.join(comic_info['tags'])}\n") if search else Plain(text=''),
                                    Plain(text=f"页数：{comic_info['pagesCount']}\n"),
                                    Plain(text=f"章节数：{comic_info['epsCount']}\n"),
                                    Plain(text=f"完结状态：{'已完结' if comic_info['finished'] else '未完结'}\n"),
                                    Plain(text=f"喜欢: {comic_info['totalLikes']}    "),
                                    Plain(text=f"浏览次数: {comic_info['totalViews']}    ")
                                ]), max_width=2160
                            )).extend([
                                Plain(text="\n发送下列命令下载：\n"),
                                Plain(text=f"转发消息形式：pica download -forward {comic_info['_id']}\n"),
                                Plain(text=f"消息图片形式：pica download -message {comic_info['_id']}\n"),
                                Plain(text=f"压缩包形式：pica download {comic_info['_id']}")
                            ])
                        )
                    )
                except Exception as e:
                    logger.error(e)
                    continue
            return MessageItem(MessageChain.create(Forward(nodeList=forward_nodes)), Normal())

        elif operation.result.asDisplay() == "rank":
            rank_time = rank_time.result.asDisplay() if rank_time.matched else "-H24"
            if rank_time not in ("-H24", "-D7", "-D30"):
                return MessageItem(
                    MessageChain.create([
                        Plain(text="错误的时间！支持的选项：\n"),
                        Plain(text="H24：24小时排行榜\n"),
                        Plain(text="D7：一周排行榜\n"),
                        Plain(text="D30：一月排行榜\n"),
                        Plain(text="命令格式：pica random -{time}")
                    ]),
                    QuoteSource()
                )
            data = (await pica.rank(rank_time[1:]))[:10]
            forward_nodes = []
            rank = 0
            for comic_info in data:
                rank += 1
                try:
                    forward_nodes.append(
                        ForwardNode(
                            senderId=bot_qq,
                            time=datetime.now(),
                            senderName="纱雾酱",
                            messageChain=(await MessageChainUtils.messagechain_to_img(
                                MessageChain.create([
                                    await PicaHandler.get_thumb(comic_info),
                                    Plain(text=f"\n排名：{rank}\n"),
                                    Plain(text=f"名称：{comic_info['title']}\n"),
                                    Plain(text=f"作者：{comic_info['author']}\n"),
                                    Plain(text=f"分类：{'、'.join(comic_info['categories'])}\n"),
                                    Plain(text=f"页数：{comic_info['pagesCount']}\n"),
                                    Plain(text=f"章节数：{comic_info['epsCount']}\n"),
                                    Plain(text=f"完结状态：{'已完结' if comic_info['finished'] else '未完结'}\n"),
                                    Plain(text=f"喜欢: {comic_info['totalLikes']}    "),
                                    Plain(text=f"浏览次数: {comic_info['totalViews']}    ")
                                ]), max_width=2160
                            )).extend([
                                Plain(text="\n发送下列命令下载：\n"),
                                Plain(text=f"转发消息形式：pica download -forward {comic_info['_id']}\n"),
                                Plain(text=f"消息图片形式：pica download -message {comic_info['_id']}\n"),
                                Plain(text=f"压缩包形式：pica download {comic_info['_id']}")
                            ])
                        )
                    )
                except Exception as e:
                    logger.error(e)
                    continue
            return MessageItem(MessageChain.create(Forward(nodeList=forward_nodes)), Normal())

    @staticmethod
    async def get_thumb(comic_info: dict) -> Image:
        if os.path.exists(f"{SEARCH_CACHE_PATH}/{comic_info['_id']}.jpg"):
            return Image(path=f"{SEARCH_CACHE_PATH}/{comic_info['_id']}.jpg")
        else:
            return Image(
                data_bytes=await pica.download_image(
                    url=f"{comic_info['thumb']['fileServer']}/static/{comic_info['thumb']['path']}",
                    path=f"{SEARCH_CACHE_PATH}/{comic_info['_id']}.jpg" if SEARCH_CACHE else None
                )
            )
