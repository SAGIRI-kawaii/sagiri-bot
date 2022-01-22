import os

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import RegexMatch, FullMatch

from sagiri_bot.utils import BuildImage
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("LuxunSaid")
channel.author("SAGIRI-kawaii")
channel.description("一个生成鲁迅说过表情包的插件，在群中发送 `鲁迅[曾经]说过 内容` 即可")

core = AppCore.get_core_instance()
config = core.get_config()

luxun_author = BuildImage(
    0, 0,
    plain_text="--鲁迅",
    font_size=30,
    font=f"{os.getcwd()}/statics/fonts/msyh.ttf",
    font_color=(255, 255, 255)
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [FullMatch("鲁迅"), FullMatch("曾经", optional=True), FullMatch("说过")],
                    {"content": RegexMatch(r".+", optional=True)}
                )
            )
        ]
    )
)
async def luxun_said(app: Ariadne, message: MessageChain, group: Group, member: Member, content: RegexMatch):
    if result := await LuxunSaid.handle(app, message, group, member, content):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class LuxunSaid(AbstractHandler):
    __name__ = "LuxunSaid"
    __description__ = "一个生成鲁迅说过表情包的插件"
    __usage__ = "在群中发送 `鲁迅[曾经]说过 内容` 即可"
    __origin__ = "https://github.com/HibiKier/zhenxun_bot"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member, content: RegexMatch):
        if content.matched:
            content = content.result.asDisplay().strip()
            A = BuildImage(
                0, 0,
                font_size=37,
                background=f'{os.getcwd()}/statics/luxun.jpg',
                font=f"{os.getcwd()}/statics/fonts/msyh.ttf"
            )
            x = ""
            if len(content) > 40:
                return MessageItem(MessageChain.create([Plain(text="太长了，鲁迅说不完...")]), QuoteSource())
            while A.getsize(content)[0] > A.w - 50:
                n = int(len(content) / 2)
                x += content[:n] + '\n'
                content = content[n:]
            x += content
            if len(x.split('\n')) > 2:
                return MessageItem(MessageChain.create([Plain(text="太长了，鲁迅说不完...")]), QuoteSource())
            A.text((int((480 - A.getsize(x.split("\n")[0])[0]) / 2), 300), x, (255, 255, 255))
            A.paste(luxun_author, (320, 400), True)
            return MessageItem(MessageChain.create([Image(data_bytes=A.pic2bytes())]), QuoteSource())
        else:
            return MessageItem(MessageChain.create([Plain(text="鲁迅说他也不知道自己要说什么")]), QuoteSource())
