import re

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.command_parse.utils import execute_setting_update, execute_grant_permission
from sagiri_bot.command_parse.utils import execute_blacklist_append, execute_blacklist_remove


saya = Saya.current()
channel = Channel.current()

channel.name("BotManagement")
channel.author("SAGIRI-kawaii")
channel.description("bot管理插件，必要插件，请勿卸载！否则会导致管理功能失效（若失效请重启机器人）")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def bot_manager_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await BotManagement.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class BotManagement(AbstractHandler):
    __name__ = "BotManagement"
    __description__ = "bot管理插件，必要插件，请勿卸载！否则会导致管理功能失效（若失效请重启机器人）"
    __usage__ = "请查看文档"

    @staticmethod
    @switch(response_administrator=True)
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text.startswith("setting -set "):
            return await execute_setting_update(group, member, message_text)
        elif re.match(r"user -grant @[1-9][0-9]{4,14} .*", message_text):
            return await execute_grant_permission(group, member, message_text)
        elif re.match(r"blacklist -add @[1-9][0-9]{4,14}", message_text):
            return await execute_blacklist_append(int(message_text[16:]), group, member)
        elif re.match(r"blacklist -add -all @[1-9][0-9]{4,14}", message_text):
            return await execute_blacklist_append(int(message_text[16:]), group, member)
        elif re.match(r"blacklist -remove @[1-9][0-9]{4,14}", message_text):
            return await execute_blacklist_remove(int(message_text[19:]), group, member)
        else:
            return None
