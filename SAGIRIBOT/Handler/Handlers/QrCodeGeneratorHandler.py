import re
import qrcode
from io import BytesIO

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await QrCodeGeneratorHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class QrCodeGeneratorHandler(AbstractHandler):
    __name__ = "QrCodeGeneratorHandler"
    __description__ = "一个生成二维码的Handler"
    __usage__ = "在群中发送 `qrcode 内容` 即可"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r"qrcode .+", message.asDisplay()):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            content = message.asDisplay()[7:]
            qrcode_img = qrcode.make(content)
            bytes_io = BytesIO()
            qrcode_img.save(bytes_io)
            return MessageItem(MessageChain.create([Image.fromUnsafeBytes(bytes_io.getvalue())]), QuoteSource(GroupStrategy()))
        else:
            return None
