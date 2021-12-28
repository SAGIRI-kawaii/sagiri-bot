# -*- coding: utf-8 -*-
import os
import threading

import yaml
from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import Group, Member, GroupMessage, FriendMessage, TempMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import *
from loguru import logger

from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.utils import online_notice, get_config
from WebManager.websocket import set_log

with open('config.yaml', 'r', encoding='utf-8') as f:
    configs = yaml.safe_load(f.read())

logger.add(f"{os.getcwd()}/log/common.log", level="INFO", retention=f"{configs['commonRetention']} days", encoding="utf-8")
logger.add(f"{os.getcwd()}/log/error.log", level="ERROR", retention=f"{configs['errorRetention']} days", encoding="utf-8")
logger.add(set_log)

core = AppCore(configs)

app = core.get_app()
bcc = core.get_bcc()
saya = core.get_saya()

ignore = ["__init__", "__pycache__"]
with saya.module_context():
    for module in os.listdir("SAGIRIBOT/Handler/Handlers"):
        if module in ignore:
            continue
        try:
            if os.path.isdir(module):
                saya.require(f"SAGIRIBOT.Handler.Handlers.{module}")
            else:
                saya.require(f"SAGIRIBOT.Handler.Handlers.{module.split('.')[0]}")
        except ModuleNotFoundError:
            pass

core.load_saya_modules()


@bcc.receiver(GroupMessage)
async def group_message_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    message_text_log = message.asDisplay().replace("\n", "\\n")
    logger.info(f"收到来自群 <{group.name}> 中成员 <{member.name}> 的消息：{message_text_log}")


@logger.catch
@bcc.receiver(ApplicationLaunched)
async def init():
    await core.bot_launch_init()
    await online_notice(app)


def management_boot():
    from WebManager.web_manager import run_api
    run_api()


if get_config("webManagerApi"):
    threading.Thread(target=management_boot, args=()).start()
    if get_config("webManagerAutoBoot"):
        import webbrowser
        webbrowser.open(f"{os.getcwd()}/WebManager/index.html")


core.launch()
