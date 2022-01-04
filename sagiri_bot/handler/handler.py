from abc import ABC
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, Member


class Handler(ABC):
    """
    handler interface，
    """

    @staticmethod
    async def handle(app, message, group, member):
        pass


class AbstractHandler(Handler):
    """
    handler Base方法，主要定义Hander默认handle方法
    """
    __name__ = ""
    __description__ = ""
    __usage__ = ""

    @staticmethod
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member): ...
