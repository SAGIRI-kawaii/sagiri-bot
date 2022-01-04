from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.utils import get_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def repeater(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await Repeater.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class Repeater(AbstractHandler):
    """
    复读Handler
    """
    __name__ = "Repeater"
    __description__ = "一个复读Handler"
    __usage__ = "有两条以上相同信息时自动触发"

    group_repeat = {}
    
    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        group_id = group.id
        message_serialization = message.asPersistentString()
        if await get_setting(group_id, Setting.repeat):
            if group_id in Repeater.group_repeat.keys():
                Repeater.group_repeat[group.id]["lastMsg"] = Repeater.group_repeat[group.id]["thisMsg"]
                Repeater.group_repeat[group.id]["thisMsg"] = message_serialization
                if Repeater.group_repeat[group.id]["lastMsg"] != Repeater.group_repeat[group.id]["thisMsg"]:
                    Repeater.group_repeat[group.id]["stopMsg"] = ""
                else:
                    if Repeater.group_repeat[group.id]["thisMsg"] != Repeater.group_repeat[group.id]["stopMsg"]:
                        Repeater.group_repeat[group.id]["stopMsg"] = Repeater.group_repeat[group.id]["thisMsg"]
                        return MessageItem(message.asSendable(), Normal())
            else:
                Repeater.group_repeat[group_id] = {"lastMsg": "", "thisMsg": message_serialization, "stopMsg": ""}

        return None
