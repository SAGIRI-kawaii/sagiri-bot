import random

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.static_datas import pero_dog_contents
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal


class PeroDogHandler(AbstractHandler):
    __name__ = "PeroDogHandler"
    __description__ = "一个获取舔狗日记的Handler"
    __usage__ = "在群中发送 `舔` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "舔":
            set_result(message, MessageItem(
                MessageChain.create([Plain(text=random.choice(pero_dog_contents).replace('*', ''))]),
                Normal(GroupStrategy())
            ))
        else:
            return None
