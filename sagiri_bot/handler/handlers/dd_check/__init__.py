from graia.scheduler import timers
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.saya import SchedulerSchema
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexResult, WildcardMatch

from sagiri_bot.core.app_core import AppCore
from .utils import get_reply, update_vtb_list
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("DDCheck")
channel.author("SAGIRI-kawaii")
channel.description("一个查成分的插件")

config = AppCore.get_core_instance().get_config()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/查成分"), WildcardMatch() @ "username"])],
        decorators=[
            FrequencyLimit.require("dd_check", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH)
        ]
    )
)
async def dd_check(app: Ariadne, group: Group, message: MessageChain, username: RegexResult):
    if not username.result.asDisplay().strip():
        return await app.sendGroupMessage(group, MessageChain("空白名怎么查啊kora！"), quote=message.getFirst(Source))
    res = await get_reply(username.result.asDisplay().strip())
    await app.sendGroupMessage(
        group,
        MessageChain(res if isinstance(res, str) else [Image(data_bytes=res)]),
        quote=message.getFirst(Source)
    )


@channel.use(SchedulerSchema(timer=timers.every_custom_hours(3)))
async def dd_check_schedule():
    await update_vtb_list()
