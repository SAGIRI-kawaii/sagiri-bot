import re

from graiax import silkcoder
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Voice, Source
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import WildcardMatch, RegexResult
from graia.ariadne.message.parser.twilight import Twilight, SpacePolicy, ArgumentMatch, ArgResult

from .utils import aget_voice
from shared.utils.module_related import get_command
from shared.utils.control import (
    Config,
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()
channel.name("Speak")
channel.author("nullqwertyuiop")
channel.author("SAGIRI-kawaii")
channel.description("语音合成插件，在群中发送 `说 {content}` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module).space(SpacePolicy.FORCE),
                ArgumentMatch("-v", "--voice", type=int, optional=True) @ "voice_type",
                WildcardMatch().flags(re.DOTALL) @ "content",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("speak", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            Config.require("functions.tencent.secret_id"),
            Config.require("functions.tencent.secret_key"),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def speak(app: Ariadne, group: Group, voice_type: ArgResult, content: RegexResult, source: Source):
    text = content.result.display
    voice_type = voice_type.result if voice_type.matched else 101016
    if voice := await aget_voice(text, voice_type):
        if isinstance(voice, str):
            await app.send_group_message(group, MessageChain(voice), quote=source)
        elif isinstance(voice, bytes):
            await app.send_group_message(
                group,
                MessageChain(Voice(data_bytes=await silkcoder.async_encode(voice, rate=24000))),
            )
