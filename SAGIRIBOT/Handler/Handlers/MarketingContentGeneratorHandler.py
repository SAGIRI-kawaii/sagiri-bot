import re

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
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
    if result := await MarketingContentGeneratorHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class MarketingContentGeneratorHandler(AbstractHandler):
    __name__ = "MarketingContentGeneratorHandler"
    __description__ = "一个营销号生成器Handler"
    __usage__ = "在群中发送 `营销号#事件主体#事件内容#事件另一种说法` 即可"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match("营销号#.*#.*#.*", message.asDisplay()):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            _, somebody, something, other_word = message.asDisplay().split("#")
            content = f"""{somebody}{something}是怎么回事呢？{somebody}相信大家都很熟悉，但是{somebody}{something}是怎么回事呢，下面就让小编带大家一起了解下吧。\n{somebody}{something}，其实就是{somebody}{other_word}，大家可能会很惊讶{somebody}怎么会{something}呢？但事实就是这样，小编也感到非常惊讶。\n这就是关于{somebody}{something}的事情了，大家有什么想法呢，欢迎在评论区告诉小编一起讨论哦！ """
            return MessageItem(MessageChain.create([Plain(text=content)]), QuoteSource(GroupStrategy()))
        else:
            return None
