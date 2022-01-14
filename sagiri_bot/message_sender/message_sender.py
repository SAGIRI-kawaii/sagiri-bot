import traceback
from typing import Union
from loguru import logger
from pydantic import BaseModel
from abc import ABC, abstractmethod
from aiohttp.client_exceptions import ClientResponseError

from graia.ariadne.app import Ariadne
from graia.ariadne.exception import AccountMuted
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member, Friend

from .message_item import MessageItem
from .strategy import Strategy, DoNothing
from sagiri_bot.exception_resender import ExceptionReSender

try:
    from sagiri_bot.handler.handlers.repeater import Repeater
    has_sagiri_repeater = True
except ImportError:
    has_sagiri_repeater = False
    Repeater = None


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
            if has_sagiri_repeater:
                if target_field.id in Repeater.group_repeat.keys():
                    Repeater.group_repeat[target_field.id]["lastMsg"] = Repeater.group_repeat[target_field.id]["thisMsg"]
                    Repeater.group_repeat[target_field.id]["thisMsg"] = message.asPersistentString()
                else:
                    Repeater.group_repeat[target_field.id] = {
                        "lastMsg": "",
                        "thisMsg": message.asPersistentString(),
                        "stopMsg": ""
                    }
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
