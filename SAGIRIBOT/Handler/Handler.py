from loguru import logger
from abc import ABC, abstractmethod
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import Group, Member
from graia.application.message.chain import MessageChain


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
    Handler Base方法，主要定义Hander默认handle方法
    """
    _next_hander = None
    __name__ = ""
    __description__ = ""
    __usage__ = ""
    group: Group = None
    member: Member = None

    def __init__(self):
        logger.info(f"Create handler -> {self.__name__}")

    def set_next(self, handler):
        self._next_hander = handler
        return handler

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member): ...
