# -*- coding: utf-8 -*-
import os
import yaml
import threading
from loguru import logger

from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.event.messages import Group, Member, GroupMessage

# from SAGIRIBOT.Handler.Handlers import *
from WebManager.websocket import set_log
from SAGIRIBOT.Core.AppCore import AppCore
# from SAGIRIBOT.MessageSender.globals import res
from SAGIRIBOT.utils import online_notice, get_config
# from SAGIRIBOT.Handler.MessageHandler import GroupMessageHandler
# from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

with open('config.yaml', 'r', encoding='utf-8') as f:
    configs = yaml.load(f.read())

logger.add(f"{os.getcwd()}/log/common.log", level="INFO", retention=f"{configs['commonRetention']} days", encoding="utf-8")
logger.add(f"{os.getcwd()}/log/error.log", level="ERROR", retention=f"{configs['errorRetention']} days", encoding="utf-8")
logger.add(set_log)

core = AppCore(configs)

app = core.get_app()
bcc = core.get_bcc()
saya = core.get_saya()

with saya.module_context():
    for module in os.listdir("SAGIRIBOT/Handler/Handlers"):
        try:
            if os.path.isdir(module):
                saya.require(f"SAGIRIBOT.Handler.Handlers.{module}")
            else:
                saya.require(f"SAGIRIBOT.Handler.Handlers.{module.split('.')[0]}")
        except ModuleNotFoundError:
            pass

# g_handler: GroupMessageHandler = GroupMessageHandler([
#     ChatRecordHandler(),
#     BotManagementHandler(),
#     StatusPresenterHandler(),
#     ImageSenderHandler(),
#     TrendingHandler(),
#     PeroDogHandler(),
#     StylePictureGeneraterHandler(),
#     AvatarFunPicHandler(),
#     # AbbreviatedPredictionHandler(),
#     PDFSearchHandler(),
#     LeetcodeInfoHanlder(),
#     QrCodeGeneratorHandler(),
#     ImageSearchHandler(),
#     BiliBiliBangumiScheduleHandler(),
#     TodayInHistoryHandler(),
#     BilibiliAppParserHandler(),
#     BangumiSearchHandler(),
#     PoisonousChickenSoupHandler(),
#     PhantomTankHandler(),
#     SteamGameInfoSearchHandler(),
#     MarketingContentGeneratorHandler(),
#     ImageAdderHandler(),
#     NetworkCompilerHandler(),
#     BangumiInfoSearchHandler(),
#     JLUCSWNoticeHandler(),
#     AbstractMessageTransformHandler(),
#     LoliconKeywordSearchHandler(),
#     GroupWordCloudGeneratorHandler(),
#     KeywordReplyHandler(),
#     ChatReplyHandler(),
#     RepeaterHandler()
# ])

core.load_saya_modules()


@bcc.receiver(GroupMessage)
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    message_text_log = message.asDisplay().replace("\n", "\\n")
    logger.info(f"收到来自群 <{group.name}> 中成员 <{member.name}> 的消息：{message_text_log}")
#     if await g_handler.handle(app, message, group, member):
#         if result := res[message[Source][0].id]:
#             g_sender: GroupMessageSender = GroupMessageSender(result.strategy)
#             await g_sender.send(app, result.message, message, group, member)


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
