import re

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member

from SAGIRIBOT.utils import get_setting
from SAGIRIBOT.ORM.Tables import Setting
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal


class RepeaterHandler(AbstractHandler):
    """
    复读Handler
    """
    __name__ = "RepeaterHandler"
    __description__ = "一个复读Handler"
    __usage__ = "有两条以上相同信息时自动触发"

    __group_repeat = {}
    
    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        group_id = group.id
        message_serialization = message.asSerializationString()
        message_serialization = message_serialization.replace(
            "[mirai:source:" + re.findall(r'\[mirai:source:(.*?)]', message_serialization, re.S)[0] + "]",
            ""
        )
        if await get_setting(group_id, Setting.repeat):
            if group_id in self.__group_repeat.keys():
                self.__group_repeat[group.id]["lastMsg"] = self.__group_repeat[group.id]["thisMsg"]
                self.__group_repeat[group.id]["thisMsg"] = message_serialization
                if self.__group_repeat[group.id]["lastMsg"] != self.__group_repeat[group.id]["thisMsg"]:
                    self.__group_repeat[group.id]["stopMsg"] = ""
                else:
                    if self.__group_repeat[group.id]["thisMsg"] != self.__group_repeat[group.id]["stopMsg"]:
                        self.__group_repeat[group.id]["stopMsg"] = self.__group_repeat[group.id]["thisMsg"]
                        return MessageItem(message.asSendable(), Normal(GroupStrategy()))
            else:
                self.__group_repeat[group_id] = {"lastMsg": "", "thisMsg": message_serialization, "stopMsg": ""}

        return await super().handle(app, message, group, member)
