# -*- coding: utf-8 -*-
import os
import yaml
import time
import asyncio
from loguru import logger

from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.Handler.Handlers import *
from SAGIRIBOT.utils import online_notice
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.MessageSender.globals import res
from SAGIRIBOT.Handler.MessageHandler import GroupMessageHandler
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

logger.add(f"{os.getcwd()}/log/common.log", level="INFO", retention="7 days", encoding="utf-8")
logger.add(f"{os.getcwd()}/log/error.log", level="ERROR", retention="14 days", encoding="utf-8")

with open('config.yaml', 'r', encoding='utf-8') as f:
    configs = yaml.load(f.read())

core = AppCore(configs)

app = core.get_app()
bcc = core.get_bcc()


"""
职责链模式，可自行调整Handler顺序，顺序执行
其中
    ChatRecordHandler 建议放在第一个，不会中途跳出，处理后继续向下
    RepeaterHandler 建议放在最后一个，防止复读其他Handler的指令
可自由增减Handler
"""
g_handler: GroupMessageHandler = GroupMessageHandler([
    ChatRecordHandler(),
    BotManagementHandler(),
    StatusPresenterHandler(),
    ImageSenderHandler(),
    TrendingHandler(),
    StylePictureGeneraterHandler(),
    AvatarFunPicHandler(),
    AbbreviatedPredictionHandler(),
    PDFSearchHandler(),
    LeetcodeInfoHanlder(),
    QrCodeGeneratorHandler(),
    ImageSearchHandler(),
    BiliBiliBangumiScheduleHandler(),
    TodayInHistoryHandler(),
    BilibiliAppParserHandler(),
    BangumiSearchHandler(),
    PhantomTankHandler(),
    SteamGameInfoSearchHandler(),
    MarketingContentGeneratorHandler(),
    NetworkCompilerHandler(),
    BangumiInfoSearchHandler(),
    JLUCSWNoticeHandler(),
    GroupWordCloudGeneratorHandler(),
    KeywordReplyHandler(),
    ChatReplyHandler(),
    RepeaterHandler()
])

core.load_saya_modules()


@bcc.receiver(GroupMessage)
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    # print("s:", time.time())
    message_text_log = message.asDisplay().replace("\n", "\\n")
    logger.info(f"收到来自群 <{group.name}> 中成员 <{member.name}> 的消息：{message_text_log}")
    if await g_handler.handle(app, message, group, member):
        result = res[message[Source][0].id]
        g_sender: GroupMessageSender = GroupMessageSender(result.strategy)
        await g_sender.send(app, result.message, message, group, member)
    # print("e:", time.time())


@logger.catch
@bcc.receiver(ApplicationLaunched)
async def init():
    await core.bot_launch_init()
    await online_notice(app)


core.launch()

