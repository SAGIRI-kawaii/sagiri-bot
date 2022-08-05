# -*- coding: utf-8 -*-
import os
import threading
from loguru import logger
from datetime import time
from pathlib import Path

from creart import create
from graia.saya import Saya
from graia.broadcast import Broadcast
from graia.ariadne.event.lifecycle import ApplicationLaunch
from graia.ariadne.event.message import ActiveFriendMessage, ActiveGroupMessage
from graia.ariadne.event.message import Group, Member, MessageChain, Friend, Stranger

from sagiri_bot.config import GlobalConfig
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.internal_utils import online_notice
from sagiri_bot.core.api_server.app import run_api_server, set_log

config = create(GlobalConfig)
core = AppCore(config)
app = core.get_app()
bcc = create(Broadcast)
saya = create(Saya)

logger.add(
    Path(os.getcwd()) / "log" / "{time:YYYY-MM-DD}" / "common.log",
    level="INFO",
    retention=f"{config.log_related['common_retention']} days",
    encoding="utf-8",
    rotation=time(),
)
logger.add(
    Path(os.getcwd()) / "log" / "{time:YYYY-MM-DD}" / "error.log",
    level="ERROR",
    retention=f"{config.log_related['error_retention']} days",
    encoding="utf-8",
    rotation=time(),
)
# logger.add(set_log)

ignore = ["__init__.py", "__pycache__"]
with saya.module_context():
    for module in os.listdir("sagiri_bot/handler/handlers"):
        if module in ignore:
            continue
        try:
            if os.path.isdir(module):
                saya.require(f"sagiri_bot.handler.handlers.{module}")
            else:
                saya.require(f"sagiri_bot.handler.handlers.{module.split('.')[0]}")
        except ModuleNotFoundError:
            logger.exception("")

core.load_saya_modules()


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
    logger.info(f"收到来自群 <{member.group.name.strip()}> 中成员 <{member.name.strip()}> 的临时消息：{message_text_log}")


@bcc.receiver("StrangerMessage")
async def stranger_message_listener(stranger: Stranger, message: MessageChain):
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(f"收到来自陌生人 <{stranger.nickname.strip()}> 的消息：{message_text_log}")


@bcc.receiver("ActiveGroupMessage")
async def send_group_message_handler(event: ActiveGroupMessage):
    message_text_log = event.message_chain.display.replace("\n", "\\n").strip()
    logger.info(f"成功向群 <{event.subject.name.strip()}> 发送消息：{message_text_log}")


@bcc.receiver("ActiveFriendMessage")
async def send_group_message_handler(event: ActiveFriendMessage):
    message_text_log = event.message_chain.display.replace("\n", "\\n").strip()
    logger.info(f"成功向好友 <{event.subject.nickname.strip()}> 发送消息：{message_text_log}")


@bcc.receiver(ApplicationLaunch)
async def init():
    await core.bot_launch_init()
    await online_notice(app)


threading.Thread(target=run_api_server, args=()).start()
core.launch()
