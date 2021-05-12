import re

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.command_parse.utils import execute_setting_update, execute_grant_permission


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await BotManagementHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class BotManagementHandler(AbstractHandler):
    __name__ = "BotManagementHandler"
    __description__ = "bot管理Handler"
    __usage__ = "请查看文档"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text.startswith("setting -set "):
            return await execute_setting_update(group, member, message_text)
        elif re.match(r"user -grant @[1-9][0-9]{4,14} .*", message_text):
            return await execute_grant_permission(group, member, message_text)
        else:
            return None
