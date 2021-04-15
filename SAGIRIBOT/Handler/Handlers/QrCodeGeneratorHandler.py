import re
import qrcode
from io import BytesIO

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Image

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount


class QrCodeGeneratorHandler(AbstractHandler):
    __name__ = "QrCodeGeneratorHandler"
    __description__ = "一个生成二维码的Handler"
    __usage__ = "在群中发送 `qrcode 内容` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r"qrcode .+", message.asDisplay()):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            content = message.asDisplay()[7:]
            qrcode_img = qrcode.make(content)
            bytes_io = BytesIO()
            qrcode_img.save(bytes_io)
            set_result(message, MessageItem(MessageChain.create([Image.fromUnsafeBytes(bytes_io.getvalue())]), QuoteSource(GroupStrategy())))
            # return MessageItem(MessageChain.create([Image.fromUnsafeBytes(bytes_io.getvalue())]), QuoteSource(GroupStrategy()))
        else:
            return None
            # return await super().handle(app, message, group, member)
