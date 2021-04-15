import re

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.command_parse.utils import execute_setting_update, execute_grant_permission


class BotManagementHandler(AbstractHandler):
    __name__ = "BotManagementHandler"
    __description__ = "bot管理Handler"
    __usage__ = "请查看文档"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text.startswith("setting -set "):
            set_result(message, await execute_setting_update(group, member, message_text))
        elif re.match(r"user -grant @[1-9][0-9]{4,14} .*", message_text):
            set_result(message, await execute_grant_permission(group, member, message_text))
        else:
            return None
