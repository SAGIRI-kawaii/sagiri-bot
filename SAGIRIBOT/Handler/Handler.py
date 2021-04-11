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

    async def handle(self, app, message, group, member):
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

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        self.group = group
        self.member = member
        if self._next_hander:
            return await self._next_hander.handle(app, message, group, member)
        return None


class HeadHandler(AbstractHandler):
    """
    HeadHandler，作为职责链起点
    """
    _next_hander = None
    __name__ = "HeadHandler"

    def set_next(self, handler):
        self._next_hander = handler
        return handler

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if self._next_hander:
            return await self._next_hander.handle(app, message, group, member)
        return None

