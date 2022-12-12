from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, GroupMessage, ActiveGroupMessage
from graia.ariadne.message.element import (
    Image,
    Plain,
    At,
    Quote,
    AtAll,
    Face,
    Poke,
    Forward,
    App,
    Json,
    Xml,
    MarketFace,
    MultimediaElement,
)

from shared.orm.tables import Setting
from shared.models.group_setting import GroupSetting
from shared.utils.control import Function, Distribute

channel = Channel.current()
channel.name("Repeater")
channel.author("SAGIRI-kawaii, nullqwertyuiop")
channel.description("一个复读插件，有两条以上相同信息时自动触发")

group_repeat = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[Distribute.distribute(), Function.require(channel.module, log=False)],
    )
)
async def repeater_handler(app: Ariadne, message: MessageChain, group: Group):
    group_setting = create(GroupSetting)
    if not await group_setting.get_setting(group, Setting.switch):
        return
    global group_repeat
    if (
        message.has(Forward)
        or message.has(App)
        or message.has(Json)
        or message.has(Xml)
        or message.has(MarketFace)
    ):
        group_repeat[group.id] = {"msg": message.as_persistent_string(), "count": -1}
        return
    msg = message.copy()
    for i in msg.__root__:
        if isinstance(i, MultimediaElement):
            i.url = ""
    message_serialization = msg.as_persistent_string()
    if group.id not in group_repeat.keys():
        group_repeat[group.id] = {"msg": message_serialization, "count": 1}
    elif message_serialization == group_repeat[group.id]["msg"]:
        if group_repeat[group.id]["count"] == -1:
            return
        count = group_repeat[group.id]["count"] + 1
        if count == 2:
            group_repeat[group.id]["count"] = count
            msg = message.include(Plain, Image, At, Quote, AtAll, Face, Poke)
            if msg.display == "<! 不支持的消息类型 !>":
                group_repeat[group.id] = {
                    "msg": msg.as_persistent_string(),
                    "count": -1,
                }
                return
            msg = msg.as_sendable()
            if msg.__root__:
                return await app.send_group_message(group, msg)
        else:
            group_repeat[group.id]["count"] = count
            return
    else:
        group_repeat[group.id]["msg"] = message_serialization
        group_repeat[group.id]["count"] = 1


@channel.use(ListenerSchema(listening_events=[ActiveGroupMessage]))
async def repeater_flush_handler(event: ActiveGroupMessage):
    global group_repeat
    group_repeat[event.subject.id] = {
        "msg": event.message_chain.as_persistent_string(),
        "count": -1,
    }
