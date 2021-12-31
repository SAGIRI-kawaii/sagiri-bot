import re
import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from SAGIRIBOT.utils import get_setting
from SAGIRIBOT.ORM.AsyncORM import Setting
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def dice_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await DiceHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class DiceHandler(AbstractHandler):
    __name__ = "DiceHandler"
    __description__ = "投骰子"
    __usage__ = "None"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(r"[0-9]+d[0-9]+", message.asDisplay()):
            if not await get_setting(group.id, Setting.dice):
                return MessageItem(MessageChain.create([Plain(text="骰子功能尚未开启哟~")]), QuoteSource(GroupStrategy()))
            times, max_point = message.asDisplay().strip().split('d')
            times, max_point = int(times), int(max_point)
            if times > 100:
                return MessageItem(MessageChain.create([Plain(text="nmd，太多次了！")]), QuoteSource(GroupStrategy()))
            elif max_point > 1000:
                return MessageItem(MessageChain.create([Plain(text="你的太大，我忍不住！")]), QuoteSource(GroupStrategy()))
            else:
                return MessageItem(MessageChain.create([
                    Plain(text=f"{random.choice([num for num in range(1, max_point + 1)])}/{max_point} ") for _ in range(times)
                ]), QuoteSource(GroupStrategy()))
