from aiohttp import ClientSession

from creart import create
from graia.saya import Channel
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.saya.builtins.broadcast import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, UnionMatch, RegexResult

from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)
from sagiri_bot.config import GlobalConfig
from .util import ALL_EMOJI, get_mix_emoji_url

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
                    UnionMatch(*ALL_EMOJI) @ "emoji1",
                    FullMatch("+"),
                    UnionMatch(*ALL_EMOJI) @ "emoji2",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("emoji_mix", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def emoji_mix(
    app: Ariadne, event: GroupMessage, emoji1: RegexResult, emoji2: RegexResult
):
    emoji1: str = emoji1.result.display
    emoji2: str = emoji2.result.display
    try:
        async with ClientSession() as session:
            assert (link := get_mix_emoji_url(emoji1, emoji2)), "无法获取合成链接"
            async with session.get(link, proxy=proxy) as resp:
                assert resp.status == 200, "图片获取失败"
                image = await resp.read()
                return await app.send_group_message(
                    event.sender.group, MessageChain([Image(data_bytes=image)])
                )
    except AssertionError as err:
        err_text = err.args[0]
    except Exception as err:
        err_text = str(err)
    return await app.send_group_message(
        event.sender.group, MessageChain([Plain(err_text)])
    )
