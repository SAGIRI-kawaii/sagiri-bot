import random

from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.parser.twilight import RegexMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema

from shared.orm import Setting
from shared.models.group_setting import GroupSetting
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("Dice")
channel.author("SAGIRI-kawaii")
channel.description("一个简单的投骰子插件，发送 `{times}d{range}` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"[0-9]+d[0-9]+$")])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("dice", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def dice(app: Ariadne, message: MessageChain, group: Group, source: Source):
    times, max_point = message.display.strip().split("d")
    times, max_point = int(times), int(max_point)
    if times > 100:
        await app.send_group_message(group, MessageChain("nmd，太多次了！"), quote=source)
    elif max_point > 1000:
        await app.send_group_message(group, MessageChain("你滴太大，我忍不住！"), quote=source)
    else:
        await app.send_group_message(
            group,
            MessageChain([f"{random.choice(list(range(1, max_point + 1)))}/{max_point} " for _ in range(times)]),
            quote=source
        )
