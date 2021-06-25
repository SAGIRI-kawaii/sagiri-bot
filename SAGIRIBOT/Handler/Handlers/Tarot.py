import os
import json
import random
from pathlib import Path
from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await TarotHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class TarotHandler(AbstractHandler):
    __name__ = "TarotHandler"
    __description__ = "可以抽塔罗牌的Handler"
    __usage__ = "None"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "塔罗牌":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return await TarotHandler.get_tarot()
        else:
            return None

    @staticmethod
    async def get_tarot():
        card, filename = TarotHandler.get_random_tarot()
        dir = random.choice(['normal', 'reverse'])
        type = '正位' if dir == 'normal' else '逆位'
        content = f"{card['name']} ({card['name-en']}) {type}\n牌意：{card['meaning'][dir]}"
        elements = []
        img_path = f"{os.getcwd()}/statics/tarot/{dir}/{filename + '.jpg'}"
        if filename and os.path.exists(img_path):
            elements.append(Image.fromLocalFile(img_path))
        elements.append(Plain(text=content))
        return MessageItem(MessageChain.create(elements), QuoteSource(GroupStrategy()))

    @staticmethod
    def get_random_tarot():
        path = f"{os.getcwd()}/statics/tarot/tarot.json"
        with open(path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        kinds = ['major', 'pentacles', 'wands', 'cups', 'swords']
        cards = []
        for kind in kinds:
            cards.extend(data[kind])
        card = random.choice(cards)
        filename = ''
        for kind in kinds:
            if card in data[kind]:
                filename = '{}{:02d}'.format(kind, card['num'])
                break
        return card, filename
