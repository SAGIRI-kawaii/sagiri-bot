from creart import create
from graia.scheduler import timers
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.saya import SchedulerSchema
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import UnionMatch, RegexResult, WildcardMatch

from sagiri_bot.config import GlobalConfig
from .utils import get_reply, update_vtb_list
from sagiri_bot.internal_utils import get_plugin_config,get_command_match
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("DDCheck")
channel.author("SAGIRI-kawaii")
channel.description("一个查成分的插件")

config = create(GlobalConfig)
plugin_config = get_plugin_config(channel.module)
prefix = plugin_config.get("prefix")
alias = plugin_config.get("alias")
alias.append("查成分")
command = UnionMatch(*get_command_match(prefix, alias))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([command, WildcardMatch() @ "username"])],
        decorators=[
            FrequencyLimit.require("dd_check", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH)
        ]
    )
)
async def dd_check(app: Ariadne, group: Group, source: Source, username: RegexResult):
    if not username.result.display.strip():
        return await app.send_group_message(group, MessageChain("空白名怎么查啊kora！"), quote=source)
    res = await get_reply(username.result.display.strip())
    await app.send_group_message(
        group,
        MessageChain(res if isinstance(res, str) else [Image(data_bytes=res)]),
        quote=source
    )


@channel.use(SchedulerSchema(timer=timers.every_custom_hours(3)))
async def dd_check_schedule():
    await update_vtb_list()
