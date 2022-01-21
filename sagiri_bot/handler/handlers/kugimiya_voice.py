import os
import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Voice
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.pattern import FullMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("KugimiyaVoice")
channel.author("SAGIRI-kawaii")
channel.description("一个钉宫语音包插件，发送 `来点钉宫` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([FullMatch("来点钉宫")]))]
    )
)
async def kugimiya_voice(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await KugimiyaVoice.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class KugimiyaVoice(AbstractHandler):
    __name__ = "KugimiyaVoice"
    __description__ = "一个钉宫语音包插件"
    __usage__ = "发送 `来点钉宫` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        base_path = f"{os.getcwd()}/statics/voice/kugimiya/"
        path = base_path + random.sample(os.listdir(base_path), 1)[0]
        return MessageItem(MessageChain.create([Voice(path=path)]), Normal())
