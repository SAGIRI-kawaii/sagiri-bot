import re
import qrcode
from io import BytesIO

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
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

channel.name("QrcodeGenerator")
channel.author("SAGIRI-kawaii")
channel.description("一个生成二维码的插件，在群中发送 `qrcode 内容` 即可（文字）")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def qrcode_generator(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await QrcodeGenerator.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class QrcodeGenerator(AbstractHandler):
    __name__ = "QrcodeGenerator"
    __description__ = "一个生成二维码的插件"
    __usage__ = "在群中发送 `qrcode 内容` 即可（文字）"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(r"qrcode .+", message.asDisplay()):
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            content = message.asDisplay()[7:]
            qrcode_img = qrcode.make(content)
            bytes_io = BytesIO()
            qrcode_img.save(bytes_io)
            return MessageItem(MessageChain.create([Image(data_bytes=bytes_io.getvalue())]), QuoteSource())
        else:
            return None
