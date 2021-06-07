# -*- coding: utf-8 -*-
import os
import yaml
import traceback
import threading
from loguru import logger

from graia.application import GraiaMiraiApplication
from graia.application.exceptions import AccountMuted
from graia.application.message.elements.internal import *
from graia.application.event.mirai import BotJoinGroupEvent
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.event.messages import Group, Member, GroupMessage

from WebManager.websocket import set_log
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.utils import online_notice, get_config
from SAGIRIBOT.ORM.AsyncORM import orm, UserPermission, Setting
from SAGIRIBOT.frequency_limit_module import GlobalFrequencyLimitDict

with open('config.yaml', 'r', encoding='utf-8') as f:
    configs = yaml.load(f.read())

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
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    message_text_log = message.asDisplay().replace("\n", "\\n")
    logger.info(f"收到来自群 <{group.name}> 中成员 <{member.name}> 的消息：{message_text_log}")


@bcc.receiver(BotJoinGroupEvent)
async def bot_join_group(app: GraiaMiraiApplication, group: Group):
    logger.info(f"机器人加入群组 <{group.name}>")
    try:
        await orm.insert_or_update(
            Setting,
            [Setting.group_id == group.id],
            {"group_id": group.id, "group_name": group.name, "active": True}
        )
        await orm.insert_or_update(
            UserPermission,
            [UserPermission.member_id == core.get_config()["HostQQ"], UserPermission.group_id == group.id],
            {"member_id": core.get_config()["HostQQ"], "group_id": group.id, "level": 4}
        )
        GlobalFrequencyLimitDict().add_group(group.id)
        await app.sendGroupMessage(
            group, MessageChain.create([
                Plain(text="欸嘿嘿~我来啦！宇宙无敌小可爱纱雾酱华丽登场！")
            ])
        )
    except AccountMuted:
        pass
    except:
        logger.error(traceback.format_exc())


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
