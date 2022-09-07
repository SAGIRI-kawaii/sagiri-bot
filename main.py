# -*- coding: utf-8 -*-
from loguru import logger

from pathlib import Path
from creart import create
from graia.saya import Saya
from graia.broadcast import Broadcast
from graia.ariadne.event.message import ActiveFriendMessage, ActiveGroupMessage
from graia.ariadne.event.message import Group, Member, MessageChain, Friend, Stranger

from core import Sagiri
from shared.funcs import online_notice
from shared.models.config import GlobalConfig
from shared.models.frequency_limit import frequency_limit

config = create(GlobalConfig)
core = create(Sagiri)
bcc = create(Broadcast)
saya = create(Saya)


@bcc.receiver("GroupMessage")
async def group_message_handler(message: MessageChain, group: Group, member: Member):
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(
        f"收到来自群 <{group.name.strip()}> 中成员 <{member.name.strip()}> 的消息：{message_text_log}"
    )


@bcc.receiver("FriendMessage")
async def friend_message_listener(friend: Friend, message: MessageChain):
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(f"收到来自好友 <{friend.nickname.strip()}> 的消息：{message_text_log}")


@bcc.receiver("TempMessage")
async def temp_message_listener(member: Member, message: MessageChain):
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(
        f"收到来自群 <{member.group.name.strip()}> 中成员 <{member.name.strip()}> 的临时消息：{message_text_log}"
    )


@bcc.receiver("StrangerMessage")
async def stranger_message_listener(stranger: Stranger, message: MessageChain):
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(f"收到来自陌生人 <{stranger.nickname.strip()}> 的消息：{message_text_log}")


@bcc.receiver("ActiveGroupMessage")
async def active_group_message_handler(event: ActiveGroupMessage):
    message_text_log = event.message_chain.display.replace("\n", "\\n").strip()
    logger.info(f"成功向群 <{event.subject.name.strip()}> 发送消息：{message_text_log}")


@bcc.receiver("ActiveFriendMessage")
async def active_friend_message_handler(event: ActiveFriendMessage):
    message_text_log = event.message_chain.display.replace("\n", "\\n").strip()
    logger.info(f"成功向好友 <{event.subject.nickname.strip()}> 发送消息：{message_text_log}")


@bcc.receiver("ApplicationLaunch")
async def init():
    await core.initialize()
    await online_notice()
    await frequency_limit()


if __name__ == '__main__':
    if Path.cwd() != Path(__file__).parent:
        logger.critical(f"当前目录非项目所在目录！请进入{str(Path(__file__).parent)}后再运行 SAGIRI-BOT!")
        exit(0)
    core.install_modules(Path("modules") / "self_contained")
    core.install_modules(Path("modules") / "required")
    core.launch()
