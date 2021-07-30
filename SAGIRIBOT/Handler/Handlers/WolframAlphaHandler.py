import aiohttp

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.utils import get_config
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def wolfram_alpha_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await WolframAlphaHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class WolframAlphaHandler(AbstractHandler):
    __name__ = "WolframAlphaHandler"
    __description__ = "一个接入WolframAlpha的Handler"
    __usage__ = "/solve 内容"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("/solve "):
            question = message.asDisplay()[7:]
            return await WolframAlphaHandler.get_result(group, member, question)

    @staticmethod
    @frequency_limit_require_weight_free(4)
    async def get_result(group: Group, member: Member, question: str) -> MessageItem:
        api_key = get_config("wolframAlphaKey")
        if api_key == "wolframAlphaKey":
            return MessageItem(MessageChain.create([Plain(text="尚未配置wolframAlphaKey！")]), QuoteSource(GroupStrategy()))
        url = f"https://api.wolframalpha.com/v1/simple?i={question.replace('+', '%2B')}&appid={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                if resp.status == 200:
                    res = await resp.read()
                    return MessageItem(MessageChain.create([Image.fromUnsafeBytes(res)]), QuoteSource(GroupStrategy()))
                else:
                    return MessageItem(MessageChain.create([Plain(text=await resp.text())]), QuoteSource(GroupStrategy()))