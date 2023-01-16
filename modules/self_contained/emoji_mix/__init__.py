from datetime import datetime

from aiohttp import ClientSession

from creart import create
from graia.ariadne.event.lifecycle import ApplicationLaunch
from graia.saya import Channel
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Forward, ForwardNode
from graia.saya.builtins.broadcast import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    UnionMatch,
    RegexResult,
    RegexMatch,
)

from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute,
)
from shared.models.config import GlobalConfig
from .util import _ALL_EMOJI, get_mix_emoji_url, get_available_pairs, _download_update

channel = Channel.current()
channel.name("EmojiMix")
channel.author("nullqwertyuiop")
channel.author("SAGIRI-kawaii")
channel.author("from: MeetWq")
channel.description("一个生成emoji融合图的插件，发送 '{emoji1}+{emoji2}' 即可")

config = create(GlobalConfig)
proxy = config.proxy if config.proxy != "proxy" else ""


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch(*_ALL_EMOJI) @ "left",
                    FullMatch("+"),
                    UnionMatch(*_ALL_EMOJI) @ "right",
                ]
            )
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("emoji_mix", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def emoji_mix(
    app: Ariadne, event: GroupMessage, left: RegexResult, right: RegexResult
):
    left: str = left.result.display
    right: str = right.result.display
    try:
        async with ClientSession() as session:
            assert (
                url := get_mix_emoji_url(left, right)
            ), f'不存在该 Emoji 组合，可以发送 "查看 emoji 组合：{left}" 查找可用组合'
            async with session.get(url, proxy=proxy) as resp:
                assert resp.status == 200, "图片下载失败"
                image: bytes = await resp.read()
                return await app.send_group_message(
                    event.sender.group, MessageChain(Image(data_bytes=image))
                )
    except AssertionError as err:
        err_text = err.args[0]
    except Exception as err:
        err_text = str(err)
    return await app.send_group_message(event.sender.group, MessageChain(err_text))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                FullMatch("查看"),
                RegexMatch(r"[eE][mM][oO][jJ][iI]"),
                FullMatch("组合"),
                RegexMatch(r"[:：] ?\S+") @ "keyword",
            )
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("emoji_mix", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def get_emoji_pair(app: Ariadne, event: GroupMessage, keyword: RegexResult):
    keyword = keyword.result.display[1:].strip()
    if pairs := get_available_pairs(keyword):
        return app.send_message(
            event.sender.group,
            MessageChain(
                Forward(
                    ForwardNode(
                        target=app.account,
                        time=datetime.now(),
                        message=MessageChain(f"可用 Emoji 组合：\n{', '.join(pairs)}"),
                        name="SAGIRI-BOT",
                    )
                )
            ),
        )
    return app.send_message(event.sender.group, MessageChain("没有可用的 Emoji 组合"))


@channel.use(ListenerSchema(listening_events=[ApplicationLaunch]))
async def fetch_emoji_update():
    await _download_update()
