import asyncio
import contextlib
from typing import Union
from abc import ABC, abstractmethod

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, At
from graia.ariadne.model import Friend, Group, Member


class Strategy(ABC):

    @abstractmethod
    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target: Union[MessageEvent, Group, Friend, Member],
        sender: Union[Friend, Member]
    ):
        pass


class QuoteSource(Strategy):
    """ 回复语句 """

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target: Union[MessageEvent, Group, Friend, Member],
        sender: Union[Friend, Member]
    ):
        await app.sendMessage(target, message, quote=origin_message[Source][0])


class Normal(Strategy):
    """ 正常发送 """

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target: Union[MessageEvent, Group, Friend, Member],
        sender: Union[Friend, Member]
    ):
        await app.sendMessage(target, message)


class AtSender(Strategy):
    """ @发送消息的人 """

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target: Union[MessageEvent, Group, Friend, Member],
        sender: Union[Friend, Member]
    ):
        message = MessageChain.create([At(target=sender.id)]).extend(message, copy=True)
        await app.sendMessage(target, message)


class Revoke(Strategy):
    """ n秒后撤回 """

    def __init__(self, delay_second: int = 20):
        self.__delay_second = delay_second

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target: Union[MessageEvent, Group, Friend, Member],
        sender: Union[Friend, Member]
    ):
        message = await app.sendMessage(target, message)
        await asyncio.sleep(self.__delay_second)
        with contextlib.suppress(UnknownTarget):
            await app.recallMessage(message)


class DoNothing(Strategy):
    """ 什么也不做 """

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target: Union[MessageEvent, Group, Friend, Member],
        sender: Union[Friend, Member]
    ):
        pass
