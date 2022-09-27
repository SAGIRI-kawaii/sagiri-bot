from enum import Enum

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import UploadMethod
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import WildcardMatch, RegexResult, ArgumentMatch, ArgResult

from .utils import handlers
from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("Music")
channel.author("SAGIRI-kawaii")
channel.description("一个获取帮助的插件，在群中发送 `/help` 即可")

DEFAULT_MUSIC_PLATFORM = "wyy"
DEFAULT_SEND_TYPE = "card"


class MusicPlatform(Enum):
    wyy = "网易云音乐"
    qq = "QQ音乐"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-p", "-platform", type=str, choices=["qq", "wyy"], optional=True) @ "music_platform",
                ArgumentMatch("-t", "-type", type=str, choices=["card", "voice", "file"], optional=True) @ "send_type",
                WildcardMatch() @ "keyword"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("music", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def music(app: Ariadne, group: Group, keyword: RegexResult, music_platform: ArgResult, send_type: ArgResult):
    music_platform = music_platform.result.display.strip() if music_platform.matched else DEFAULT_MUSIC_PLATFORM
    send_type = send_type.result if send_type.matched else DEFAULT_SEND_TYPE
    keyword = keyword.result
    element = await handlers[music_platform](keyword, send_type)
    if element:
        if isinstance(element, tuple):
            await app.upload_file(
                data=element[1],
                method=UploadMethod.Group,
                target=group,
                name=f"{element[0]}.mp3",
            )
        else:
            await app.send_group_message(group, MessageChain(element))
