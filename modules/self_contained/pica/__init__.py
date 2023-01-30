import re
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp
from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.util import UploadMethod
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Forward, ForwardNode, Image, Source
from graia.ariadne.message.parser.twilight import (
    ArgResult,
    ArgumentMatch,
    FullMatch,
    RegexResult,
    Twilight,
    UnionMatch,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member
from graia.broadcast.builtin.decorators import Depend
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from shared.models.config import GlobalConfig
from shared.utils.control import (
    BlackListControl,
    Config,
    Distribute,
    FrequencyLimit,
    Function,
    UserCalledCountControl,
)
from shared.utils.daily_number_limiter import DailyNumberLimiter
from shared.utils.module_related import get_command

from .pica import pica as pica_v
from .utils import pica_t2i, zip_directory

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
bot_qq = config.default_account
DOWNLOAD_CACHE = config.functions["pica"]["download_cache"]
SEARCH_CACHE = config.functions["pica"]["search_cache"]

BASE_PATH = Path(__file__).parent
SEARCH_CACHE_PATH = BASE_PATH / "cache" / "search"
DOWNLOAD_CACHE_PATH = BASE_PATH / "cache" / "download"
SEARCH_CACHE_PATH.mkdir(parents=True, exist_ok=True)

DAILY_DOWNLOAD_LIMIT = int(config.functions["pica"]["daily_download_limit"])
DAILY_SEARCH_LIMIT = int(config.functions["pica"]["daily_search_limit"])
DAILY_RANDOM_LIMIT = int(config.functions["pica"]["daily_random_limit"])
DAILY_RANK_LIMIT = int(config.functions["pica"]["daily_rank_limit"])

DAILY_DOWNLOAD_LIMITER = DailyNumberLimiter(DAILY_DOWNLOAD_LIMIT)
DAILY_SEARCH_LIMITER = DailyNumberLimiter(DAILY_SEARCH_LIMIT)
DAILY_RANDOM_LIMITER = DailyNumberLimiter(DAILY_RANDOM_LIMIT)
DAILY_RANK_LIMITER = DailyNumberLimiter(DAILY_RANK_LIMIT)

decorators = [
    Distribute.distribute(),
    Config.require("functions.pica.username"),
    Config.require("functions.pica.password"),
    FrequencyLimit.require("pica_function", 3),
    Function.require(channel.module, notice=True),
    BlackListControl.enable(),
    UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
]

limit = {
    "download": {
        "limiter": DAILY_DOWNLOAD_LIMITER,
        "text": "今天已经达到每日下载上限啦~\n明天再来吧~\n❤你❤这❤个❤小❤色❤批❤~",
    },
    "search": {
        "limiter": DAILY_SEARCH_LIMITER,
        "text": "今天已经达到每日搜索上限啦~\n明天再来吧~\n想找本子的话，自己去下载个哔咔好咯~",
    },
    "random": {
        "limiter": DAILY_RANDOM_LIMITER,
        "text": "今天已经达到每日随机本子上限啦~\n明天再来吧~\n你这个人对本子真是挑剔呢~",
    },
    "rank": {
        "limiter": DAILY_RANK_LIMITER,
        "text": "今天已经达到每日排行榜查询上限啦~\n明天再来吧~\n排行榜一次还看不够嘛~",
    },
}


def check_init():
    async def check_init_deco(app: Ariadne, group: Group):
        if not pica_v.init:
            return await app.send_group_message(
                group, MessageChain("pica实例初始化失败，请重启机器人或重载插件！")
            )

    return Depend(check_init_deco)


decorators_i = [*decorators, check_init()]


def check_limit(ty: str):
    limiter: DailyNumberLimiter = limit[ty]["limiter"]
    limit_text: str = limit[ty]["text"]

    async def check_limit_deco(
        app: Ariadne, group: Group, member: Member, source: Source
    ):
        if not limiter.check(member.id):
            return await app.send_group_message(
                group, MessageChain(limit_text), quote=source
            )
        limiter.increase(member.id)

    return Depend(check_limit_deco)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(get_command(__file__, channel.module), FullMatch("init"))
        ],
        decorators=decorators,
    )
)
async def pica_init(app: Ariadne, group: Group):
    if pica_v.init:
        return await app.send_group_message(group, MessageChain("pica已初始化"))
    try:
        res = await pica_v.check()
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
        decorators=[*decorators_i, check_limit("rank")],
    )
)
async def pica_rank(app: Ariadne, group: Group, rank_time: RegexResult):
    rank_type = rank_time.result.display[1:] if rank_time.result else "H24"
    data = (await pica_v.rank(rank_type))[:20]  # type: ignore
    forward_nodes = []
    for rank, comic in enumerate(data, 1):
        try:
            forward_nodes.append(
                ForwardNode(
                    sender_id=bot_qq,
                    time=datetime.now(),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(
                        await pica_t2i(await comic.get_info(), rank=rank),
                        "\n发送下列命令下载：\n"
                        f"转发消息形式：pica download -forward {comic.id}\n"
                        f"消息图片形式：pica download -message {comic.id}\n"
                        f"压缩包形式：pica download {comic.id}",
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
        decorators=[*decorators_i, check_limit("search"), check_limit("random")],
    )
)
async def pica_search(
        app: Ariadne, group: Group, operation: RegexResult, content: RegexResult
):
    search = str(operation.result) == "search"
    keyword = str(content.result).strip() if content.matched else ""
    if search and content.matched:
        await app.send_message(group, MessageChain(f"收到请求，正在搜索{keyword}..."))
    data = (await (pica_v.search(keyword) if search else pica_v.random()))[:20]
    if not data:
        return await app.send_group_message(group, MessageChain("没有搜索到捏"))

    forward_nodes = []
    for comic in data:
        comic_info = (
            await comic.get_info() if str(operation.result) == "search" else comic
        )
        forward_nodes.append(
            ForwardNode(
                sender_id=bot_qq,
                time=datetime.now(),
                sender_name="纱雾酱",
                message_chain=MessageChain(
                    await pica_t2i(comic_info),
                    "\n发送下列命令下载：\n"
                    f"转发消息形式：pica download -forward {comic_info.id}\n"
                    f"消息图片形式：pica download -message {comic_info.id}\n"
                    f"压缩包形式：pica download {comic_info.id}",
                ),
            )
        )
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
        decorators=[*decorators_i, check_limit("download")],
    )
)
async def pica_download(
        app: Ariadne, group: Group, forward_type: ArgResult, content: RegexResult
):
    if not content.matched:
        return await app.send_group_message(group, MessageChain("是要下载什么啊？"))

    comic_id = str(content.result)
    await app.send_message(group, MessageChain(f"明白，正在下载{comic_id}..."))
    comic = await pica_v.get_comic_from_id(comic_id)
    assert comic
    comic_path = DOWNLOAD_CACHE_PATH / comic.title
    comic_name = comic.title
    _ = await comic.download(DOWNLOAD_CACHE_PATH / comic.title)
    logger.info("本子下载完成！")
    if forward_type.matched:
        time_base = datetime.now() - timedelta(minutes=20)

        node_message = lambda time, message: ForwardNode(
            sender_id=bot_qq,
            time=time_base + timedelta(minutes=time),
            sender_name="纱雾酱",
            message_chain=MessageChain(message),
        )

        step = 20
        files = list(comic_path.rglob("*.*"))
        file_split = [files[i: i + step] for i in range(0, len(files), step)]
        for file in file_split:
            # oh 我的上帝，怎么能够这么套娃
            pic_node = [
                node_message(
                    n,
                    [
                        Image(path=f),
                        f"\n{f.relative_to(comic_path)}\n"
                        f"{time_base + timedelta(minutes=n)}",
                    ],
                )
                for n, f in enumerate(file)
            ]
            await app.send_group_message(
                group,
                MessageChain(
                    Forward(
                        node_list=[
                            node_message(-1, "IOS系统可能会乱序，请参照下方文件名和发送时间顺序自行排序！"),
                            *pic_node,
                        ]
                    )
                ),
            )
    else:
        await app.send_group_message(group, "下载完成，正在压缩中，可能比较耗时...")
        zip_file = zip_directory(comic_path, comic_name)
        # QQ 文件不允许出现的字符
        name = re.sub('[\\\\/:*?"<>|]', "", str(comic_name))
        try:
            await app.upload_file(
                data=zip_file,
                method=UploadMethod.Group,
                target=group,
                name=f"{name}.zip",
            )

        except RemoteException:
            await app.upload_file(
                data=zip_file,
                method=UploadMethod.Group,
                target=group,
                name=f"pica_{comic_id}.zip",
            )

        logger.info("发送完成，正在删除压缩文件")
        zip_file.unlink()
