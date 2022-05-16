from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage, ActiveGroupMessage
from graia.ariadne.message.chain import MessageChain
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
    MultimediaElement
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.control import Function
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.utils import group_setting

saya = Saya.current()
channel = Channel.current()

channel.name("Repeater")
channel.author("SAGIRI-kawaii, nullqwertyuiop")
channel.description("一个复读插件，有两条以上相同信息时自动触发")

group_repeat = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[Function.require(channel.module, log=False)],
    )
)
async def repeater_handler(app: Ariadne, message: MessageChain, group: Group):
    if not await group_setting.get_setting(
        group, Setting.repeat
    ) or not await group_setting.get_setting(group, Setting.switch):
        return
    global group_repeat
    if (
        message.has(Forward)
        or message.has(App)
        or message.has(Json)
        or message.has(Xml)
        or message.has(MarketFace)
    ):
        group_repeat[group.id] = {"msg": message.asPersistentString(), "count": -1}
        return
    msg = message.copy()
    for i in msg.__root__:
        if isinstance(i, MultimediaElement):
            i.url = ""
    message_serialization = msg.asPersistentString()
    if group.id not in group_repeat.keys():
        group_repeat[group.id] = {"msg": message_serialization, "count": 1}
    else:
        if message_serialization == group_repeat[group.id]["msg"]:
            if group_repeat[group.id]["count"] == -1:
                return
            count = group_repeat[group.id]["count"] + 1
            if count == 2:
                group_repeat[group.id]["count"] = count
                msg = message.include(Plain, Image, At, Quote, AtAll, Face, Poke)
                if msg.asDisplay() == "<! 不支持的消息类型 !>":
                    group_repeat[group.id] = {
                        "msg": msg.asPersistentString(),
                        "count": -1,
                    }
                    return
                return await app.sendGroupMessage(group, msg.asSendable())
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
        "msg": event.messageChain.asPersistentString(),
        "count": -1,
    }
