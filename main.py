# -*- coding: utf-8 -*-
import json
import yaml
from loguru import logger

from graia.application.event.messages import Group, Member
from graia.application.event.messages import GroupMessage
from graia.application.message.elements.internal import *
from graia.application import GraiaMiraiApplication
from graia.application.event.lifecycle import ApplicationLaunched

from SAGIRIBOT.Handler.Handlers import *
from SAGIRIBOT.utils import online_notice
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.Handler.MessageHandler import GroupMessageHandler
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

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
    LatexGeneratorHandler(),
    JLUCSWNoticeHandler(),
    GroupWordCloudGeneratorHandler(),
    KeywordReplyHandler(),
    ChatReplyHandler(),
    RepeaterHandler()
])


@bcc.receiver(GroupMessage)
@logger.catch
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    message_text_log = message.asDisplay().replace("\n", "\\n")
    logger.info(f"收到来自群 <{group.name}> 中成员 <{member.name}> 的消息：{message_text_log}")
    if result := await g_handler.handle(app, message, group, member):
        g_sender: GroupMessageSender = GroupMessageSender(result.strategy)
        await g_sender.send(app, result.message, message, group, member)


@logger.catch
@bcc.receiver(ApplicationLaunched)
async def init():
    await core.bot_launch_init()
    await online_notice(app)


core.launch()

