from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.utils import MessageChainUtils
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await MessageMergeHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class MessageMergeHandler(AbstractHandler):
    __name__ = "MessageMergeHandler"
    __description__ = "将收到的消息合并为图片"
    __usage__ = "在群中发送 `/merge 文字/图片`"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("/merge "):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            elements = [element for element in message.__root__ if (isinstance(element, Image) or isinstance(element, Plain))]
            elements[0].text = elements[0].text[7:]
            return MessageItem(await MessageChainUtils.messagechain_to_img(MessageChain.create(elements)), QuoteSource(GroupStrategy()))
        else:
            return None
