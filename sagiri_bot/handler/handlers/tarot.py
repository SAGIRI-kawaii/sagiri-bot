import os
import json
import random
from pathlib import Path
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount

saya = Saya.current()
channel = Channel.current()

channel.name("Tarot")
channel.author("SAGIRI-kawaii")
channel.description("可以抽塔罗牌的插件，在群中发送 `塔罗牌` 即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def tarot(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await Tarot.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class Tarot(AbstractHandler):
    __name__ = "Tarot"
    __description__ = "可以抽塔罗牌的插件"
    __usage__ = "在群中发送 `塔罗牌` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "塔罗牌":
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            return await Tarot.get_tarot()
        else:
            return None

    @staticmethod
    async def get_tarot():
        card, filename = Tarot.get_random_tarot()
        dir = random.choice(['normal', 'reverse'])
        type = '正位' if dir == 'normal' else '逆位'
        content = f"{card['name']} ({card['name-en']}) {type}\n牌意：{card['meaning'][dir]}"
        elements = []
        img_path = f"{os.getcwd()}/statics/tarot/{dir}/{filename + '.jpg'}"
        if filename and os.path.exists(img_path):
            elements.append(Image(path=img_path))
        elements.append(Plain(text=content))
        return MessageItem(MessageChain.create(elements), QuoteSource())

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
