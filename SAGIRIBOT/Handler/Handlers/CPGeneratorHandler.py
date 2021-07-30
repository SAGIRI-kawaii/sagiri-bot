import os
import re
import json
import random

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount

saya = Saya.current()
channel = Channel.current()
with open(f"{os.getcwd()}/statics/cp_data.json", "r", encoding="utf-8") as r:
    cp_data = json.loads(r.read())


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def cp_generator_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await CPGeneratorHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class CPGeneratorHandler(AbstractHandler):
    __name__ = "CPGeneratorHandler"
    __description__ = "生成CP文的Handler"
    __usage__ = "/cp 攻 受"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r"/cp \w+ \w+", message.asDisplay()):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            _, attack, defence = message.asDisplay().split(" ")
            return await CPGeneratorHandler.generate_article(attack, defence)

    @staticmethod
    async def generate_article(attack: str, defence: str) -> MessageItem:
        template = random.choice(cp_data["data"])
        content = template.replace("<攻>", attack).replace("<受>", defence)
        return MessageItem(
            MessageChain.create([
                Plain(text=content)
            ]),
            QuoteSource(GroupStrategy())
        )
