import asyncio
from pydantic import BaseModel
from abc import ABC, abstractmethod

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, At


class StrategyType(ABC):
    @abstractmethod
    async def send_method(self, app: Ariadne):
        pass


class GroupStrategy(StrategyType):
    async def send_method(self, app: Ariadne):
        return app.sendGroupMessage


class FriendStrategy(StrategyType):
    async def send_method(self, app: Ariadne):
        return app.sendFriendMessage


class TempStrategy(StrategyType):
    async def send_method(self, app: Ariadne):
        return app.sendTempMessage


class Strategy(ABC):

    __message: MessageChain = None
    __strategy_type: StrategyType = None

    @abstractmethod
    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target_field: BaseModel,
        sender: BaseModel
    ):
        pass


class QuoteSource(Strategy):
    """ 回复语句 """

    def __init__(self, strategy_type: StrategyType):
        self.__strategy_type = strategy_type

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target_field: BaseModel,
        sender: BaseModel
    ):
        await (await self.__strategy_type.send_method(app))(target_field, message, quote=origin_message[Source][0])


class Normal(Strategy):
    """ 正常发送 """

    def __init__(self, strategy_type: StrategyType):
        self.__strategy_type = strategy_type

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target_field: BaseModel,
        sender: BaseModel
    ):
        await (await self.__strategy_type.send_method(app))(target_field, message)


class AtSender(Strategy):
    """ @发送消息的人 """

    def __init__(self, strategy_type: StrategyType):
        self.__strategy_type = strategy_type

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target_field: BaseModel,
        sender: BaseModel
    ):
        message = MessageChain.create([At(target=sender.id)]).extend(message)
        await (await self.__strategy_type.send_method(app))(target_field, message)


class Revoke(Strategy):
    """ n秒后撤回 """

    def __init__(self, strategy_type: StrategyType, delay_second: int = 20):
        self.__strategy_type = strategy_type
        self.__delay_second = delay_second

    async def send(
        self,
        app: Ariadne,
        message: MessageChain,
        origin_message: MessageChain,
        target_field: BaseModel,
        sender: BaseModel
    ):
        message = await (await self.__strategy_type.send_method(app))(target_field, message)
        await asyncio.sleep(self.__delay_second)
        await app.recallMessage(message)


class DoNothing(Strategy):
    """ 什么也不做 """

    def __init__(self, strategy_type: StrategyType):
        self.__strategy_type = strategy_type

    async def send(
        self,
        app: GraiaMiraiApplication,
        message: MessageChain,
        origin_message: MessageChain,
        target_field: BaseModel,
        sender: BaseModel
    ):
        pass
