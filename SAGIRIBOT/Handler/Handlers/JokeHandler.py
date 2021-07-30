import re
import random

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource, Normal
from SAGIRIBOT.static_datas import jokes, soviet_jokes, america_jokes, french_jokes

saya = Saya.current()
channel = Channel.current()

joke_non_replace = {
    "法国": french_jokes,
    "美国": america_jokes,
    "苏联": soviet_jokes
}


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def joke_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await JokeHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class JokeHandler(AbstractHandler):
    __name__ = "JokeHandler"
    __description__ = "生成笑话"
    __usage__ = "来点xx笑话"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r"来点.+笑话", message.asDisplay()):
            keyword = message.asDisplay()[2:-2]
            if keyword in joke_non_replace.keys():
                return MessageItem(
                    MessageChain.create([Plain(text=random.choice(joke_non_replace[keyword]))]),
                    Normal(GroupStrategy())
                )
            else:
                return MessageItem(
                    MessageChain.create([Plain(text=random.choice(jokes).replace("%name%", keyword))]),
                    QuoteSource(GroupStrategy())
                )
