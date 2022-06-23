from graia.saya import Saya, Channel
from graia.ariadne import get_running
from graia.ariadne.app import Ariadne
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, RegexResult

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("WolframAlpha")
channel.author("SAGIRI-kawaii")
channel.description("一个接入WolframAlpha的插件，在群中发送 `/solve {content}` 即可")

api_key = AppCore.get_core_instance().get_config().functions.get("wolfram_alpha_key", None)


@channel.use(ListenerSchema(
    listening_events=[GroupMessage],
    inline_dispatchers=[Twilight([FullMatch("/solve"), RegexMatch(".+") @ "content"])],
    decorators=[
        FrequencyLimit.require("wolfram_alpha", 4),
        Function.require(channel.module, notice=True),
        BlackListControl.enable(),
        UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
    ]
))
async def wolfram_alpha(app: Ariadne, message: MessageChain, group: Group, content: RegexResult):
    question = content.result.asDisplay()
    if not api_key or api_key == "wolfram_alpha_key":
        return MessageItem(MessageChain.create([Plain(text="尚未配置wolfram_alpha_key！")]), QuoteSource())
    url = f"https://api.wolframalpha.com/v1/simple?i={question.replace('+', '%2B')}&appid={api_key}"
    async with get_running(Adapter).session.get(url=url) as resp:
        if resp.status == 200:
            res = await resp.read()
            await app.sendGroupMessage(group, MessageChain([Image(data_bytes=res)]), quote=message.getFirst(Source))
        else:
            await app.sendGroupMessage(group, MessageChain(await resp.text()), quote=message.getFirst(Source))
