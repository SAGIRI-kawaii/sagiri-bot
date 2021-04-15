import traceback
from loguru import logger
from pydantic import BaseModel
from abc import ABC, abstractmethod
from aiohttp.client_exceptions import ClientResponseError

from graia.application import GraiaMiraiApplication
from graia.application.exceptions import AccountMuted
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Source

from .MessageItem import MessageItem
from .Strategy import Strategy, DoNoting
from SAGIRIBOT.MessageSender.globals import res
from SAGIRIBOT.exception_resender import ExceptionReSender
from SAGIRIBOT.Core.Exceptions import AsyncioTasksGetResult


class MessageSender(ABC):
    """
    MessageSender interface，
    """
    __promote: Strategy = None
    __message: MessageChain = None

    @abstractmethod
    async def send(
            self,
            app: GraiaMiraiApplication,
            message: MessageChain,
            origin_message: MessageChain,
            target_field: BaseModel,
            sender: BaseModel
    ):
        pass


class GroupMessageSender(MessageSender):
    def __init__(self, strategy: Strategy):
        self.__strategy = strategy

    async def send(
            self,
            app: GraiaMiraiApplication,
            message: MessageChain,
            origin_message: MessageChain,
            group: Group,
            member: Member
    ):
        try:
            await self.__strategy.send(app, message, origin_message, group, member)
            if not isinstance(self.__strategy, DoNoting):
                logger.success(f"成功向群 <{group.name}> 发送消息 - {message.asDisplay()}")
        except AccountMuted:
            logger.error(f"Bot 在群 <{group.name}> 被禁言，无法发送！")
        except ClientResponseError:
            logger.error(traceback.format_exc())
            ExceptionReSender().addTask([
                MessageItem(message, self.__strategy),
                origin_message,
                group,
                member,
                1
            ])
        except TypeError:
            pass


def set_result(origin_message: MessageChain, item: MessageItem):
    res[origin_message[Source][0].id] = item
    # print(res)
    raise AsyncioTasksGetResult
