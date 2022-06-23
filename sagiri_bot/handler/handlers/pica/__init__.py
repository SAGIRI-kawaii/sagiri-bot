import os
import aiohttp
from loguru import logger
from datetime import datetime, timedelta

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import UploadMethod
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import RegexResult, ArgResult
from graia.ariadne.message.element import ForwardNode, Image, Plain, Forward, Source
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, UnionMatch, ArgumentMatch

from .Pica import pica
from sagiri_bot.core.app_core import AppCore
from utils.text_engine.adapter import GraiaAdapter
from utils.text_engine.text_engine import TextEngine
from utils.daily_number_limiter import DailyNumberLimiter
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

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
            Twilight([
                FullMatch("pica"),
                UnionMatch("download", "search", "random", "rank", "init") @ "operation",
                ArgumentMatch("-forward", action="store_true", optional=True) @ "forward_type",
                ArgumentMatch("-message", action="store_true", optional=True) @ "message_type",
                UnionMatch("-H24", "-D7", "-D30", optional=True) @ "rank_time",
                RegexMatch(r".+", optional=True) @ "content"
            ])
        ],
        decorators=[
            FrequencyLimit.require("pica_function", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def pica_function(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    operation: RegexResult,
    message_type: ArgResult,
    forward_type: ArgResult,
    rank_time: RegexResult,
    content: RegexResult
):
    if not pica.init:
        await app.sendGroupMessage(group, MessageChain("pica实例初始化失败，请重启机器人或重载插件！"))
        return
    if any([
        operation.result.asDisplay() == "download" and not DAILY_DOWNLOAD_LIMITER.check(member.id),
        operation.result.asDisplay() == "search" and not DAILY_SEARCH_LIMITER.check(member.id),
        operation.result.asDisplay() == "random" and not DAILY_RANDOM_LIMITER.check(member.id),
        operation.result.asDisplay() == "rank" and not DAILY_RANK_LIMITER.check(member.id)
    ]):
        return await app.sendGroupMessage(
            group, MessageChain(limit_text[str(operation.result.asDisplay())]), quote=message.getFirst(Source)
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
            await app.sendGroupMessage(group, MessageChain("pica已初始化"))
            return
        try:
            await pica.check()
            await app.sendGroupMessage(group, MessageChain("pica初始化成功"))
        except aiohttp.ClientConnectorError:
            await app.sendGroupMessage(group, MessageChain("pica初始化失败，请检查代理"))
        except KeyError:
            await app.sendGroupMessage(group, MessageChain("pica初始化失败，请检查账号密码是否配置正确"))

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
            messageChain=MessageChain("IOS系统可能会乱序，请参照下方文件名和发送时间顺序自行排序！")
        )]
        for path in image_list:
            node_count += 1
            time_count += 1
            forward_nodes.append(
                ForwardNode(
                    senderId=bot_qq,
                    time=time_base + timedelta(seconds=time_count),
                    senderName="纱雾酱",
                    messageChain=MessageChain([
                        Image(path=path),
                        Plain(f"\n{path.replace(info[0], '')}\n{time_base + timedelta(seconds=time_count)}")
                    ])
                )
            )
            if node_count == 20:
                await app.sendMessage(group, MessageChain([Forward(nodeList=forward_nodes)]))
                forward_nodes = [
                    ForwardNode(
                        senderId=bot_qq,
                        time=time_base + timedelta(seconds=time_count),
                        senderName="纱雾酱",
                        messageChain=MessageChain("IOS系统可能会乱序，请参照下方文件名和发送时间顺序自行排序！")
                    )
                ]
                node_count = 0
        await app.sendGroupMessage(group, MessageChain([Forward(nodeList=forward_nodes)]))

    elif operation.result.asDisplay() == "download" and message_type.matched and content.matched:
        comic_id = content.result.asDisplay()
        await app.sendMessage(group, MessageChain(f"收到请求，正在下载{comic_id}..."))
        info = await pica.download_comic(comic_id, False)
        image_list = []
        for root, _, files in os.walk(info[0]):
            for file in files:
                if file[-3:] != "zip":
                    image_list.append(os.path.join(root, file))
        await app.sendGroupMessage(group, MessageChain([Image(path=path) for path in image_list]))

    elif operation.result.asDisplay() == "download" and content.matched:
        comic_id = message.asDisplay()[14:]
        await app.sendMessage(group, MessageChain(f"收到请求，正在下载{comic_id}..."))
        info = await pica.download_comic(comic_id)
        try:
            await app.uploadFile(
                data=info[1],
                method=UploadMethod.Group,
                target=group,
                name=f"{info[0].replace(' ', '')}.zip"
            )
        except RemoteException:
            await app.uploadFile(
                data=info[1],
                method=UploadMethod.Group,
                target=group,
                name=f"pica_{comic_id}.zip"
            )
        return None

    elif operation.result.asDisplay() in ("search", "random"):
        search = operation.result.asDisplay() == "search"
        keyword = content.result.asDisplay().strip() if content.matched else ''
        if search and content.matched:
            await app.sendMessage(group, MessageChain(f"收到请求，正在搜索{keyword}..."))
        data = (await pica.search(keyword))[:10] \
            if search else (await pica.random())[:10]
        forward_nodes = []
        if not data:
            return await app.sendGroupMessage(group, MessageChain("没有搜索到捏"))
        for comic in data:
            comic_info = await pica.comic_info(comic["id"]) if operation.result.asDisplay() == "search" else comic
            try:
                forward_nodes.append(
                    ForwardNode(
                        senderId=bot_qq,
                        time=datetime.now(),
                        senderName="纱雾酱",
                        messageChain=MessageChain([
                            Image(data_bytes=TextEngine(
                                [GraiaAdapter(
                                    MessageChain([
                                        await get_thumb(comic_info),
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
                                    ])
                                )], max_width=2160
                            ).draw())
                        ]).extend([
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
        await app.sendGroupMessage(group, MessageChain([Forward(nodeList=forward_nodes)]))

    elif operation.result.asDisplay() == "rank":
        rank_time = rank_time.result.asDisplay() if rank_time.matched else "-H24"
        if rank_time not in ("-H24", "-D7", "-D30"):
            await app.sendGroupMessage(
                group, MessageChain([
                    Plain(text="错误的时间！支持的选项：\n"),
                    Plain(text="H24：24小时排行榜\n"),
                    Plain(text="D7：一周排行榜\n"),
                    Plain(text="D30：一月排行榜\n"),
                    Plain(text="命令格式：pica random -{time}")
                ])
            )
            return
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
                        messageChain=MessageChain([
                            Image(data_bytes=TextEngine(
                                [GraiaAdapter(
                                    MessageChain([
                                        await get_thumb(comic_info),
                                        Plain(text=f"\n排名：{rank}\n"),
                                        Plain(text=f"名称：{comic_info['title']}\n"),
                                        Plain(text=f"作者：{comic_info['author']}\n"),
                                        Plain(text=f"分类：{'、'.join(comic_info['categories'])}\n"),
                                        Plain(text=f"页数：{comic_info['pagesCount']}\n"),
                                        Plain(text=f"章节数：{comic_info['epsCount']}\n"),
                                        Plain(text=f"完结状态：{'已完结' if comic_info['finished'] else '未完结'}\n"),
                                        Plain(text=f"喜欢: {comic_info['totalLikes']}    "),
                                        Plain(text=f"浏览次数: {comic_info['totalViews']}    ")
                                    ])
                                )], max_width=2160
                            ).draw())
                        ]).extend([
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
        await app.sendGroupMessage(group, MessageChain([Forward(nodeList=forward_nodes)]))


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
