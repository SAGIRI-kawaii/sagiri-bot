import re

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.utils import get_setting
from SAGIRIBOT.ORM.AsyncORM import Setting
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def repeater_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await RepeaterHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class RepeaterHandler(AbstractHandler):
    """
    复读Handler
    """
    __name__ = "RepeaterHandler"
    __description__ = "一个复读Handler"
    __usage__ = "有两条以上相同信息时自动触发"

    group_repeat = {}
    
    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        group_id = group.id
        message_serialization = message.asSerializationString()
        message_serialization = message_serialization.replace(
            "[mirai:source:" + re.findall(r'\[mirai:source:(.*?)]', message_serialization, re.S)[0] + "]",
            ""
        )
        if await get_setting(group_id, Setting.repeat):
            if group_id in RepeaterHandler.group_repeat.keys():
                RepeaterHandler.group_repeat[group.id]["lastMsg"] = RepeaterHandler.group_repeat[group.id]["thisMsg"]
                RepeaterHandler.group_repeat[group.id]["thisMsg"] = message_serialization
                if RepeaterHandler.group_repeat[group.id]["lastMsg"] != RepeaterHandler.group_repeat[group.id]["thisMsg"]:
                    RepeaterHandler.group_repeat[group.id]["stopMsg"] = ""
                else:
                    if RepeaterHandler.group_repeat[group.id]["thisMsg"] != RepeaterHandler.group_repeat[group.id]["stopMsg"]:
                        RepeaterHandler.group_repeat[group.id]["stopMsg"] = RepeaterHandler.group_repeat[group.id]["thisMsg"]
                        return MessageItem(message.asSendable(), Normal(GroupStrategy()))
            else:
                RepeaterHandler.group_repeat[group_id] = {"lastMsg": "", "thisMsg": message_serialization, "stopMsg": ""}

        return None
