import re

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.control import BlackListControl, Switch
from sagiri_bot.command_parse.utils import (
    execute_setting_update,
    execute_grant_permission,
)
from sagiri_bot.command_parse.utils import (
    execute_blacklist_append,
    execute_blacklist_remove,
)


saya = Saya.current()
channel = Channel.current()

channel.name("BotManagement")
channel.author("SAGIRI-kawaii")
channel.description("bot管理插件，必要插件，请勿卸载！否则会导致管理功能失效（若失效请重启机器人）")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            Switch.enable(response_administrator=True),
            BlackListControl.enable(),
        ],
    )
)
async def bot_manager_handler(
    app: Ariadne, message: MessageChain, group: Group, member: Member, source: Source
):
    message_text = message.display
    if message_text.startswith("setting -set "):
        msg = await execute_setting_update(group, member, message_text)
    elif re.match(r"user -grant @[1-9][0-9]{4,14} .*", message_text):
        msg = await execute_grant_permission(group, member, message_text)
    elif re.match(r"blacklist -add @[1-9][0-9]{4,14}", message_text):
        msg = await execute_blacklist_append(int(message_text[16:]), group, member)
    elif re.match(r"blacklist -add -all @[1-9][0-9]{4,14}", message_text):
        msg = await execute_blacklist_append(int(message_text[16:]), group, member)
    elif re.match(r"blacklist -remove @[1-9][0-9]{4,14}", message_text):
        msg = await execute_blacklist_remove(int(message_text[19:]), group, member)
    else:
        return None
    await app.send_group_message(group, msg, quote=source)
