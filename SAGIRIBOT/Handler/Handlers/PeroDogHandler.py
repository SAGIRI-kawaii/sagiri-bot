import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.static_datas import pero_dog_contents
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await PeroDogHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class PeroDogHandler(AbstractHandler):
    __name__ = "PeroDogHandler"
    __description__ = "一个获取舔狗日记的Handler"
    __usage__ = "在群中发送 `舔` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "舔":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return MessageItem(
                MessageChain.create([Plain(text=random.choice(pero_dog_contents).replace('*', ''))]),
                Normal(GroupStrategy())
            )
        else:
            return None
