from io import BytesIO
import matplotlib.pyplot as plt

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource


class LatexGeneratorHandler(AbstractHandler):
    __name__ = "LatexGeneratorHandler"
    __description__ = "一个latex公式转图片的Handler"
    __usage__ = "/latex 公式"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("/latex "):
            str_latex = f"${message.asDisplay()[7:]}$"
            return await self.formula2img(str_latex)
        else:
            return await super().handle(app, message, group, member)

    @staticmethod
    async def formula2img(str_latex, img_size=(5, 3), font_size=20) -> MessageItem:
        fig = plt.figure(figsize=img_size)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.text(0.5, 0.5, str_latex, fontsize=font_size, verticalalignment='center', horizontalalignment='center')
        bytes_io = BytesIO()
        plt.savefig(bytes_io)
        return MessageItem(MessageChain.create([Image.fromUnsafeBytes(bytes_io.getvalue())]), QuoteSource(GroupStrategy()))
