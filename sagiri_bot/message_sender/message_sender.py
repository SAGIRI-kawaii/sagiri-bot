import traceback
from typing import Union
from loguru import logger
from pydantic import BaseModel
from abc import ABC, abstractmethod
from aiohttp.client_exceptions import ClientResponseError

from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.exception import AccountMuted
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member, Friend

from .message_item import MessageItem
from .strategy import Strategy, DoNothing
from sagiri_bot.exception_resender import ExceptionReSender
from sagiri_bot.core.exceptions import AsyncioTasksGetResult


# class MessageSender1:
#     """
#     message_sender interface，
#     """
#     promote: Strategy = None
#     message: MessageChain = None
#
#     def __init__(self, strategy: Strategy):
#         self.__promote = strategy
#
#     async def send(
#             self,
#             app: Ariadne,
#             message: MessageChain,
#             origin_message: MessageChain,
#             target_field: Union[MessageEvent, Group, Friend, Member],
#             sender: Union[Member, Friend]
#     ):
#         try:
#             await self.__promote.send(app, message, origin_message, target_field, sender)
#         except AccountMuted:
#             logger.error(f"Bot 在群 <{target_field.name}> 被禁言，无法发送！")
#         except ClientResponseError:
#             logger.error(traceback.format_exc())
#             ExceptionReSender().addTask([
#                 MessageItem(message, self.__promote),
#                 origin_message,
#                 target_field,
#                 sender,
#                 1
#             ])
#         except TypeError:
#             pass


class MessageSender:
    promote: Strategy = DoNothing()
    message: MessageChain = None

    def __init__(self, strategy: Strategy):
        self.__strategy = strategy

    async def send(
            self,
            app: Ariadne,
            message: MessageChain,
            origin_message: MessageChain,
            target_field: Union[MessageEvent, Group, Friend, Member],
            sender: Union[Friend, Member]
    ):
        try:
            await self.__strategy.send(app, message, origin_message, target_field, sender)
            if not isinstance(self.promote, DoNothing):
                logger.success(
                    f"成功向{'好友' if isinstance(target_field, Friend) else '群组'} "
                    f"<{target_field.name}> 发送消息 - {message.asDisplay()}"
                )
        except AccountMuted:
            logger.error(f"Bot 在群 <{target_field.name}> 被禁言，无法发送！")
        except ClientResponseError:
            logger.error(traceback.format_exc())
            ExceptionReSender().addTask([
                MessageItem(message, self.__strategy),
                origin_message,
                target_field,
                sender,
                1
            ])
        except TypeError:
            pass
