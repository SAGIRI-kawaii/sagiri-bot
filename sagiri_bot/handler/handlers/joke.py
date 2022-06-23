import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult

from statics.jokes import jokes, soviet_jokes, america_jokes, french_jokes
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("Joke")
channel.author("SAGIRI-kawaii")
channel.description("一个生成笑话的插件，在群中发送 `来点{keyword|法国|苏联|美国}笑话`")

joke_non_replace = {
    "法国": french_jokes,
    "美国": america_jokes,
    "苏联": soviet_jokes
}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("来点"), RegexMatch(r"[^\s]+") @ "keyword", FullMatch("笑话")])],
        decorators=[
            FrequencyLimit.require("joke", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def joke(app: Ariadne, group: Group, keyword: RegexResult):
    keyword = keyword.result.asDisplay()
    if keyword in joke_non_replace.keys():
        await app.sendGroupMessage(group, MessageChain(random.choice(joke_non_replace[keyword])))
    else:
        await app.sendGroupMessage(group, MessageChain(random.choice(jokes).replace("%name%", keyword)))
