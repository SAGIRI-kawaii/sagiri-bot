from datetime import datetime, timedelta
from pathlib import Path

import aiohttp
from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.util import UploadMethod
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Forward, ForwardNode, Image, Plain, Source
from graia.ariadne.message.parser.twilight import (
    ArgResult,
    ArgumentMatch,
    FullMatch,
    RegexMatch,
    RegexResult,
    Twilight,
    UnionMatch,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger
from sagiri_bot.config import GlobalConfig
from sagiri_bot.control import (
    BlackListControl,
    FrequencyLimit,
    Function,
    UserCalledCountControl,
)
from sagiri_bot.internal_utils import get_command
from utils.daily_number_limiter import DailyNumberLimiter

from .Pica import pica
from .utils import pica_t2i, zip_directory

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

config = create(GlobalConfig)
bot_qq = config.bot_qq
DOWNLOAD_CACHE = config.functions["pica"]["download_cache"]
SEARCH_CACHE = config.functions["pica"]["search_cache"]

BASE_PATH = Path(__file__).parent
SEARCH_CACHE_PATH = BASE_PATH / "cache" / "search"
SEARCH_CACHE_PATH.mkdir(parents=True, exist_ok=True)

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
    "rank": "今天已经达到每日排行榜查询上限啦~\n明天再来吧~\n排行榜一次还看不够嘛~",
}

decorators = [
    FrequencyLimit.require("pica_function", 3),
    Function.require(channel.module, notice=True),
    BlackListControl.enable(),
    UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
]


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([get_command(__file__, channel.module), FullMatch("init")])
        ],
        decorators=decorators,
    )
)
async def pica_init(app: Ariadne, group: Group):
    if pica.init:
        return await app.send_group_message(group, MessageChain("pica已初始化"))
    try:
        res = await pica.check()
        return await app.send_group_message(
            group, MessageChain("pica初始化成功" if res else "pica实例初始化失败，请重启机器人或重载插件！")
        )
    except aiohttp.ClientConnectorError:
        await app.send_group_message(group, MessageChain("pica初始化失败，请检查代理"))
    except KeyError:
        await app.send_group_message(group, MessageChain("pica初始化失败，请检查账号密码是否配置正确"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    get_command(__file__, channel.module),
                    FullMatch("rank"),
                    UnionMatch("-H24", "-D7", "-D30") @ "rank_time",
                ]
            )
        ],
        decorators=decorators,
    )
)
async def pica_rank(
    app: Ariadne, group: Group, member: Member, rank_time: RegexResult, source: Source
):
    if not DAILY_RANK_LIMITER.check(member.id):
        return await app.send_group_message(
            group, MessageChain(limit_text["rank"]), quote=source
        )
    DAILY_RANK_LIMITER.increase(member.id)

    if not pica.init:
        return await app.send_group_message(
            group, MessageChain("pica实例初始化失败，请重启机器人或重载插件！")
        )

    rank_type = rank_time.result.display[1:] if rank_time.result else "H24"
    data = (await pica.rank(rank_type))[:10]  # type: ignore
    forward_nodes = []
    for rank, comic_info in enumerate(data, 1):
        try:
            forward_nodes.append(
                ForwardNode(
                    sender_id=bot_qq,
                    time=datetime.now(),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(
                        [
                            await pica_t2i(comic_info, rank=rank),
                            "\n发送下列命令下载：\n"
                            f"转发消息形式：pica download -forward {comic_info['_id']}\n"
                            f"消息图片形式：pica download -message {comic_info['_id']}\n"
                            f"压缩包形式：pica download {comic_info['_id']}",
                        ]
                    ),
                )
            )
        except Exception as e:
            logger.error(e)
            continue
    await app.send_group_message(
        group, MessageChain([Forward(node_list=forward_nodes)])
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    get_command(__file__, channel.module),
                    UnionMatch("search", "random") @ "operation",
                    ArgumentMatch("-forward", action="store_true", optional=True),
                    WildcardMatch() @ "content",
                ]
            )
        ],
        decorators=decorators,
    )
)
async def pica_search(
    app: Ariadne,
    group: Group,
    member: Member,
    operation: RegexResult,
    content: RegexResult,
    source: Source,
):

    if any(
        [
            str(operation.result) == "search"
            and not DAILY_SEARCH_LIMITER.check(member.id),
            str(operation.result) == "random"
            and not DAILY_RANDOM_LIMITER.check(member.id),
        ]
    ):
        return await app.send_group_message(
            group, MessageChain(limit_text[str(operation.result)]), quote=source
        )

    if str(operation.result) == "search":
        DAILY_SEARCH_LIMITER.increase(member.id)
    elif str(operation.result) == "random":
        DAILY_RANDOM_LIMITER.increase(member.id)

    if not pica.init:
        return await app.send_group_message(
            group, MessageChain("pica实例初始化失败，请重启机器人或重载插件！")
        )

    search = str(operation.result) == "search"
    keyword = str(content.result).strip() if content.matched else ""
    if search and content.matched:
        await app.send_message(group, MessageChain(f"收到请求，正在搜索{keyword}..."))
    data = (await (pica.search(keyword) if search else pica.random()))[:10]
    if not data:
        return await app.send_group_message(group, MessageChain("没有搜索到捏"))

    forward_nodes = []
    for comic in data:
        comic_info = (
            await pica.comic_info(comic["id"])
            if str(operation.result) == "search"
            else comic
        )
        try:
            forward_nodes.append(
                ForwardNode(
                    sender_id=bot_qq,
                    time=datetime.now(),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(
                        [
                            await pica_t2i(comic_info, is_search=search),
                            "\n发送下列命令下载：\n"
                            f"转发消息形式：pica download -forward {comic_info['_id']}\n"
                            f"消息图片形式：pica download -message {comic_info['_id']}\n"
                            f"压缩包形式：pica download {comic_info['_id']}",
                        ]
                    ),
                )
            )
        except Exception as e:
            logger.error(e)
            continue
    await app.send_group_message(
        group, MessageChain([Forward(node_list=forward_nodes)])
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    get_command(__file__, channel.module),
                    FullMatch("download"),
                    ArgumentMatch("-forward", action="store_true", optional=True)
                    @ "forward_type",
                    ArgumentMatch("-message", action="store_true", optional=True)
                    @ "message_type",
                    WildcardMatch() @ "content",
                ]
            )
        ],
        decorators=decorators,
    )
)
async def pica_download(
    app: Ariadne,
    group: Group,
    message: MessageChain,
    member: Member,
    source: Source,
    operation: RegexResult,
    forward_type: ArgResult,
    content: RegexResult,
):
    if not DAILY_DOWNLOAD_LIMITER.check(member.id):
        return await app.send_group_message(
            group, MessageChain(limit_text["download"]), quote=source
        )

    DAILY_DOWNLOAD_LIMITER.increase(member.id)

    if not pica.init:
        return await app.send_group_message(
            group, MessageChain("pica实例初始化失败，请重启机器人或重载插件！")
        )

    if not content.matched:
        return await app.send_group_message(group, MessageChain("是要下载什么啊？"))

    comic_id = str(content.result)
    await app.send_message(group, MessageChain(f"明白，正在下载{comic_id}..."))
    comic_path, comic_name = await pica.download_comic(comic_id)

    if forward_type.matched:
        node_count = 0
        time_base = datetime.now() - timedelta(seconds=len(list(comic_path.rglob("*"))))
        forward_nodes = [
            ForwardNode(
                sender_id=bot_qq,
                time=time_base,
                sender_name="纱雾酱",
                message_chain=MessageChain("IOS系统可能会乱序，请参照下方文件名和发送时间顺序自行排序！"),
            )
        ]
        for time_count, path in enumerate(comic_path.rglob("*"), 1):
            node_count += 1
            forward_nodes.append(
                ForwardNode(
                    sender_id=bot_qq,
                    time=time_base + timedelta(seconds=time_count),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(
                        [
                            Image(path=path),
                            Plain(
                                f"\n{path.relative_to(comic_path)}\n{time_base + timedelta(seconds=time_count)}"
                            ),
                        ]
                    ),
                )
            )
            if node_count == 20:
                await app.send_message(
                    group, MessageChain([Forward(node_list=forward_nodes)])
                )
                forward_nodes = [
                    ForwardNode(
                        sender_id=bot_qq,
                        time=time_base + timedelta(seconds=time_count),
                        sender_name="纱雾酱",
                        message_chain=MessageChain("IOS系统可能会乱序，请参照下方文件名和发送时间顺序自行排序！"),
                    )
                ]
                node_count = 0
        await app.send_group_message(
            group, MessageChain([Forward(node_list=forward_nodes)])
        )

    else:
        zip_dir = zip_directory(comic_path, comic_name)
        try:
            await app.upload_file(
                data=zip_dir,
                method=UploadMethod.Group,
                target=group,
                name=f"{str(comic_name).replace(' ', '')}.zip",
            )
        except RemoteException:
            await app.upload_file(
                data=zip_dir,
                method=UploadMethod.Group,
                target=group,
                name=f"pica_{comic_id}.zip",
            )
