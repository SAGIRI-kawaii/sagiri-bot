import asyncio

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.chain import MessageChain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ArgumentMatch,
    ArgResult,
    RegexMatch,
    RegexResult,
    ElementMatch,
    ElementResult
)

from .utils import gen_verification
from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

saya = create(Saya)
channel = Channel.current()

channel.name("GoogleVerification")
channel.author("SAGIRI-kawaii")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-e", "--en", "--english", action="store_true", optional=True) @ "en",
                RegexMatch(".+") @ "title",
                FullMatch("\n", optional=True),
                ElementMatch(Image) @ "image"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("google_verification", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ]
    )
)
async def google_verification(app: Ariadne, group: Group, en: ArgResult, title: RegexResult, image: ElementResult):
    title = title.result.display.strip()
    await app.send_group_message(
        group, MessageChain(
            Image(
                data_bytes=await asyncio.to_thread(
                    gen_verification, title, await image.result.get_bytes(), "en" if en.matched else "zh"
                )
            )
        )
    )
