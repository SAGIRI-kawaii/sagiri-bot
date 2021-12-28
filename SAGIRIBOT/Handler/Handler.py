from loguru import logger
from abc import ABC, abstractmethod
from graia.ariadne.app import Ariadne, Friend
from graia.ariadne.event.message import Group, Member
from graia.ariadne.message.chain import MessageChain


class Handler(ABC):
    """
    Handler interface，
    """

    @abstractmethod
    def set_next(self, handler):
        pass

    @staticmethod
    async def handle(app, message, group, member):
        pass


class AbstractHandler(Handler):
    """
    Handler Base方法，主要定义Handler默认handle方法
    """
    _next_handler = None
    __name__ = ""
    __description__ = ""
    __usage__ = ""
    group: Group = None
    member: Member = None

    def __init__(self):
        logger.info(f"Create handler -> {self.__name__}")

    def set_next(self, handler):
        self._next_handler = handler
        return handler

    @staticmethod
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member): ...
