import re
import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import QuoteSource, Normal
from statics.jokes import jokes, soviet_jokes, america_jokes, french_jokes

saya = Saya.current()
channel = Channel.current()

channel.name("Joke")
channel.author("SAGIRI-kawaii")
channel.description("一个生成笑话的插件，在群中发送 `来点{keyword|法国|苏联|美国}笑话`")

joke_non_replace = {
    "法国": french_jokes,
    "美国": america_jokes,
    "苏联": soviet_jokes
}


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def joke(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await Joke.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class Joke(AbstractHandler):
    __name__ = "Joke"
    __description__ = "一个生成笑话的插件"
    __usage__ = "在群中发送 `来点{keyword|法国|苏联|美国}笑话`"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(r"来点.+笑话", message.asDisplay()):
            keyword = message.asDisplay()[2:-2]
            if keyword in joke_non_replace.keys():
                return MessageItem(
                    MessageChain.create([Plain(text=random.choice(joke_non_replace[keyword]))]),
                    Normal()
                )
            else:
                return MessageItem(
                    MessageChain.create([Plain(text=random.choice(jokes).replace("%name%", keyword))]),
                    QuoteSource()
                )
