import re

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
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

channel.name("MarketingContentGenerator")
channel.author("SAGIRI-kawaii")
channel.description("一个营销号内容生成器插件，在群中发送 `营销号#事件主体#事件内容#事件另一种说法` 即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def marketing_content_generator(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await MarketingContentGenerator.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class MarketingContentGenerator(AbstractHandler):
    __name__ = "MarketingContentGenerator"
    __description__ = "一个营销号内容生成器插件"
    __usage__ = "在群中发送 `营销号#事件主体#事件内容#事件另一种说法` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match("营销号#.*#.*#.*", message.asDisplay()):
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            _, somebody, something, other_word = message.asDisplay().split("#")
            content = f"""{somebody}{something}是怎么回事呢？{somebody}相信大家都很熟悉，但是{somebody}{something}是怎么回事呢，下面就让小编带大家一起了解下吧。\n{somebody}{something}，其实就是{somebody}{other_word}，大家可能会很惊讶{somebody}怎么会{something}呢？但事实就是这样，小编也感到非常惊讶。\n这就是关于{somebody}{something}的事情了，大家有什么想法呢，欢迎在评论区告诉小编一起讨论哦！ """
            return MessageItem(MessageChain.create([Plain(text=content)]), QuoteSource())
        else:
            return None
