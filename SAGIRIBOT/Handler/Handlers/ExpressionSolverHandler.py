from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource


class ExpressionSolverHandler(AbstractHandler):
    __name__ = "ExpressionSolverHandler"
    __description__ = "可以解数学表达式的Handler"
    __usage__ = "在群中发送 `solve 表达式` 即可"

    pass
