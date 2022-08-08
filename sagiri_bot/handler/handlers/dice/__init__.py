import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.parser.twilight import RegexMatch
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.internal_utils import group_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("Dice")
channel.author("SAGIRI-kawaii")
channel.description("一个简单的投骰子插件，发送 `{times}d{range}` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"[0-9]+d[0-9]+$")])],
        decorators=[
            FrequencyLimit.require("dice", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def dice(app: Ariadne, message: MessageChain, group: Group, source: Source):
    if not await group_setting.get_setting(group.id, Setting.dice):
        await app.send_group_message(group, MessageChain("骰子功能尚未开启哟~"), quote=source)
        return
    times, max_point = message.display.strip().split("d")
    times, max_point = int(times), int(max_point)
    if times > 100:
        await app.send_group_message(group, MessageChain("nmd，太多次了！"), quote=source)
    elif max_point > 1000:
        await app.send_group_message(group, MessageChain("你滴太大，我忍不住！"), quote=source)
    else:
        await app.send_group_message(
            group,
            MessageChain(
                f"{random.choice(list(range(1, max_point + 1)))}/{max_point} "
                for _ in range(times)
            ),
            quote=source,
        )
