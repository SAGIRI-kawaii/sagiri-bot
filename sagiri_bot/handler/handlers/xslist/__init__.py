from graia.ariadne import Ariadne
from graia.saya import Saya, Channel
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    FullMatch,
    WildcardMatch,
    RegexResult,
    ElementMatch,
    ElementResult,
    RegexMatch
)

from .xslist import search
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("XsList")
channel.author("SAGIRI-kawaii")
channel.description("一个查老师的插件，发送 `/查老师 {作品名/老师名/图片}` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/查老师"), RegexMatch(r"[\s]+", optional=True),
                ElementMatch(Image, optional=True) @ "image",
                WildcardMatch(optional=True) @ "keyword"
            ])
        ],
        decorators=[
            FrequencyLimit.require("xslist", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def xslist_handler(app: Ariadne, group: Group, keyword: RegexResult, image: ElementResult):
    if image.matched:
        await app.sendGroupMessage(group, await search(data_bytes=await image.result.get_bytes()))
    elif keyword.matched:
        keyword = keyword.result.asDisplay().strip()
        await app.sendGroupMessage(group, await search(keyword=keyword))
    else:
        await app.sendGroupMessage(group, MessageChain("什么都没有，你让我查什么好呢~"))
