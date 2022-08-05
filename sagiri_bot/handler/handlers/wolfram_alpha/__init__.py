import aiohttp

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, RegexResult

from sagiri_bot.config import GlobalConfig
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("WolframAlpha")
channel.author("SAGIRI-kawaii")
channel.description("一个接入WolframAlpha的插件，在群中发送 `/solve {content}` 即可")

api_key = create(GlobalConfig).functions.get("wolfram_alpha_key", None)


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
async def wolfram_alpha(app: Ariadne, group: Group, content: RegexResult, source: Source):
    question = content.result.display
    if not api_key or api_key == "wolfram_alpha_key":
        return await app.send_group_message(group, MessageChain("尚未配置wolfram_alpha_key！"), quote=source)
    url = f"https://api.wolframalpha.com/v1/simple?i={question.replace('+', '%2B')}&appid={api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            if resp.status == 200:
                res = await resp.read()
                await app.send_group_message(group, MessageChain([Image(data_bytes=res)]), quote=source)
            else:
                await app.send_group_message(group, MessageChain(await resp.text()), quote=source)
