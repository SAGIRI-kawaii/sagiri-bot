from loguru import logger
from abc import ABC, abstractmethod
import traceback

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from .Handlers.HeadHandler import HeadHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy
from SAGIRIBOT.MessageSender.Strategy import QuoteSource
from SAGIRIBOT.Core.AppCore import AppCore


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
    __chain_names = []
    __head_handler = None

    def __init__(self, chain: list):
        self.__chain = chain
        head = HeadHandler()
        self.__head_handler = head
        node = head
        for handler in chain:
            node = node.set_next(handler)
            self.__chain_names.append(handler.__name__)
        AppCore.get_core_instance().set_group_chain(self.__chain)
        logger.success("\n----------------------------------------------\n职责链加载成功，目前链序：\n" + "\n".join([f"{handler.__name__.ljust(40) + handler.__description__}" for handler in self.__chain]) + "\n----------------------------------------------")

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        try:
            if result := await self.__head_handler.handle(app, message, group, member):
                return result
            else:
                return None
        except Exception as e:
            logger.error(traceback.format_exc())
            # return MessageItem(MessageChain.create([Plain(text="Error")]), QuoteSource(GroupStrategy()))
            # return MessageItem(MessageChain.create([Plain(text=traceback.format_exc())]), QuoteSource(GroupStrategy()))
            pass


class FriendMessageHandler(AbstractMessageHandler):
    pass


class TempMessageHandler(AbstractMessageHandler):
    pass
