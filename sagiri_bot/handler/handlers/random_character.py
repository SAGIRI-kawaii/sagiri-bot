import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from statics.character_dict import character_dict
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("RandomCharacter")
channel.author("SAGIRI-kawaii")
channel.description("随机生成人设插件，在群中发送 `随机人设` 即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def random_character(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await RandomCharacter.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class RandomCharacter(AbstractHandler):
    __name__ = "RandomCharacter"
    __description__ = "随机生成人设插件"
    __usage__ = "在群中发送 `随机人设` 即可"

    @staticmethod
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "随机人设":
            return MessageItem(MessageChain.create([Plain(text=RandomCharacter.get_rand())]), QuoteSource())

    @staticmethod
    def get_rand() -> str:
        return "\n".join([f"{k}：{random.choice(character_dict[k])}" for k in character_dict.keys()])
