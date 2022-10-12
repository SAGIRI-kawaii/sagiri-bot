from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.service import get_dist_map
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("About")
channel.author("SAGIRI-kawaii")
channel.description("一些关于bot的信息，在群中发送 `关于` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("about", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def about(app: Ariadne, group: Group):
    await app.send_group_message(
        group, MessageChain(
            "SAGIRI-BOT: V4.0.0\n"
            f"mirai-http-api: {await app.get_version()}\n" +
            "\n".join([f"{k}: {v}" for k, v in get_dist_map().items()]) +
            f"\n当前在线bot数量: {len(await app.get_bot_list())}"
        )
    )
