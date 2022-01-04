import re
import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.utils import get_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("Dice")
channel.author("SAGIRI-kawaii")
channel.description("一个简单的投骰子插件，发送 `{times}d{range}` 即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def dice_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await Dice.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class Dice(AbstractHandler):
    __name__ = "Dice"
    __description__ = "一个简单的投骰子插件"
    __usage__ = "发送 `{times}d{range}` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(r"[0-9]+d[0-9]+", message.asDisplay()):
            if not await get_setting(group.id, Setting.dice):
                return MessageItem(MessageChain.create([Plain(text="骰子功能尚未开启哟~")]), QuoteSource())
            times, max_point = message.asDisplay().strip().split('d')
            times, max_point = int(times), int(max_point)
            if times > 100:
                return MessageItem(MessageChain.create([Plain(text="nmd，太多次了！")]), QuoteSource())
            elif max_point > 1000:
                return MessageItem(MessageChain.create([Plain(text="你的太大，我忍不住！")]), QuoteSource())
            else:
                return MessageItem(MessageChain.create([
                    Plain(text=f"{random.choice([num for num in range(1, max_point + 1)])}/{max_point} ") for _ in range(times)
                ]), QuoteSource())
