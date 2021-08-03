import random

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def random_wife_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await RandomWifeHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class RandomWifeHandler(AbstractHandler):
    __name__ = "RandomWifeHandler"
    __description__ = "随机老婆"
    __usage__ = "None"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() in ("来个老婆", "随机老婆"):
            return await RandomWifeHandler.get_random_wife()

    @staticmethod
    @frequency_limit_require_weight_free(4)
    async def get_random_wife():
        return MessageItem(
            MessageChain.create([Image.fromNetworkAddress(f"https://www.thiswaifudoesnotexist.net/example-{random.randint(1, 100000)}.jpg")]),
            QuoteSource(GroupStrategy())
        )
