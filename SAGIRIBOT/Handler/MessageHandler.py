import asyncio
import traceback
from loguru import logger
from abc import ABC, abstractmethod

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Source

from SAGIRIBOT.Core.AppCore import AppCore
from .Handlers.HeadHandler import HeadHandler
from SAGIRIBOT.Core.Exceptions import AsyncioTasksGetResult
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.Core.Exceptions import FrequencyLimitExceeded
from SAGIRIBOT.Core.Exceptions import FrequencyLimitExceededDoNothing
from SAGIRIBOT.Handler.Handlers.RepeaterHandler import RepeaterHandler
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.Handler.Handlers.ChatReplyHandler import ChatReplyHandler
from SAGIRIBOT.Core.Exceptions import FrequencyLimitExceededAddBlackList
from SAGIRIBOT.MessageSender.MessageSender import set_result, set_result_without_raise


class MessageHandler(ABC):
    """
    MessageHandler interface，
    """

    @abstractmethod
    async def handle(self, app, message, group, member):
        pass


class AbstractMessageHandler(MessageHandler):
    __chain = []
    __head_handler = None

    @abstractmethod
    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        pass


class GroupMessageHandler(AbstractMessageHandler):
    __chain = []
    __handlers = []
    __chain_names = []
    __head_handler = None

    def __init__(self, chain: list):
        self.__chain = chain
        head = HeadHandler()
        self.__head_handler = head
        # node = head
        for handler in chain:
            # node = node.set_next(handler)
            self.__handlers.append(handler.handle)
            self.__chain_names.append(handler.__name__)
        AppCore.get_core_instance().set_group_chain(self.__handlers)
        logger.success("\n----------------------------------------------\n加载成功，目前加载Handler：\n" + "\n".join([f"{handler.__name__.ljust(40) + handler.__description__}" for handler in self.__chain]) + "\n----------------------------------------------")

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member) -> bool:
        repeat_handler = None
        chat_record_handler = None
        tasks = []
        for handler in self.__chain:
            if isinstance(handler, ChatReplyHandler):
                chat_record_handler = handler
            if isinstance(handler, RepeaterHandler):
                repeat_handler = handler
            else:
                tasks.append(handler.handle(app, message, group, member))
        if chat_record_handler:
            await chat_record_handler.handle(app, message, group, member)
        g = asyncio.gather(*tasks)
        try:
            await g
        except AsyncioTasksGetResult:
            g.cancel()
            return True
        except FrequencyLimitExceededDoNothing:
            g.cancel()
            return False
        except FrequencyLimitExceeded:
            g.cancel()
            set_result_without_raise(
                message,
                MessageItem(
                    MessageChain.create([Plain(text="Frequency limit exceeded every 10 seconds!")]),
                    QuoteSource(GroupStrategy())
                )
            )
            return True
        except FrequencyLimitExceededAddBlackList:
            g.cancel()
            set_result_without_raise(
                message,
                MessageItem(
                    MessageChain.create([Plain(text="检测到大量请求，警告一次，加入黑名单一小时!")]),
                    QuoteSource(GroupStrategy())
                )
            )
            return True
        if repeat_handler:
            try:
                await repeat_handler.handle(app, message, group, member)
            except AsyncioTasksGetResult:
                return True
        return False


class FriendMessageHandler(AbstractMessageHandler):
    pass


class TempMessageHandler(AbstractMessageHandler):
    pass
