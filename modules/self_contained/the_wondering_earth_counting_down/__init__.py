import asyncio

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.chain import MessageChain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    ArgResult,
    ArgumentMatch
)

from .utils import gen_counting_down, gen_gif
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

channel.name("WonderingEarthCountingDown")
channel.author("SAGIRI-kawaii")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-t", "-top") @ "top",
                ArgumentMatch("-s", "-start") @ "start",
                ArgumentMatch("-c", "-count") @ "count",
                ArgumentMatch("-e", "-end") @ "end",
                ArgumentMatch("-b", "-bottom") @ "bottom",
                ArgumentMatch("-rgba", optional=True, action="store_true") @ "rgba",
                ArgumentMatch("-gif", optional=True, action="store_true") @ "gif"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("wandering_earth_counting_down", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ]
    )
)
async def wandering_earth_counting_down(
    app: Ariadne, group: Group, top: ArgResult, start: ArgResult, count: ArgResult, end: ArgResult, bottom: ArgResult,
    rgba: ArgResult, gif: ArgResult
):
    top = top.result.display.strip("\"").strip("'")
    start = start.result.display.strip("\"").strip("'")
    count = count.result.display.strip("\"").strip("'")
    end = end.result.display.strip("\"").strip("'")
    bottom = bottom.result.display.strip("\"").strip("'")
    if gif.matched and not count.isnumeric():
        return await app.send_group_message(group, MessageChain("生成 gif 时 count 必须为数字！"))
    elif gif.matched and int(count) > 100:
        return await app.send_group_message(group, MessageChain("生成 gif 时 count 最大仅支持100！"))
    content = await asyncio.to_thread(
        gen_gif if gif.matched else gen_counting_down, top, start, count, end, bottom, rgba.matched
    )
    await app.send_group_message(group, MessageChain(Image(data_bytes=content)))
