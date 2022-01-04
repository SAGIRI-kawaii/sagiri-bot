import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.utils import get_config
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free

saya = Saya.current()
channel = Channel.current()

channel.name("WolframAlpha")
channel.author("SAGIRI-kawaii")
channel.description("一个接入WolframAlpha的插件，在群中发送 `/solve {content}` 即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def wolfram_alpha(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await WolframAlpha.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class WolframAlpha(AbstractHandler):
    __name__ = "WolframAlpha"
    __description__ = "一个接入WolframAlpha的插件"
    __usage__ = "在群中发送 `/solve {content}` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("/solve "):
            question = message.asDisplay()[7:]
            return await WolframAlpha.get_result(group, member, question)

    @staticmethod
    @frequency_limit_require_weight_free(4)
    async def get_result(group: Group, member: Member, question: str) -> MessageItem:
        api_key = get_config("wolframAlphaKey")
        if api_key == "wolframAlphaKey":
            return MessageItem(MessageChain.create([Plain(text="尚未配置wolframAlphaKey！")]), QuoteSource())
        url = f"https://api.wolframalpha.com/v1/simple?i={question.replace('+', '%2B')}&appid={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                if resp.status == 200:
                    res = await resp.read()
                    return MessageItem(MessageChain.create([Image(data_bytes=res)]), QuoteSource())
                else:
                    return MessageItem(MessageChain.create([Plain(text=await resp.text())]), QuoteSource())
