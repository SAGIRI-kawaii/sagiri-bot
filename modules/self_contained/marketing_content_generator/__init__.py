from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, RegexResult

from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()
channel.name("MarketingContentGenerator")
channel.author("SAGIRI-kawaii")
channel.description("一个营销号内容生成器插件，在群中发送 `营销号#事件主体#事件内容#事件另一种说法` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                FullMatch("#"),
                RegexMatch(r"[^\s]+") @ "somebody",
                FullMatch("#"),
                RegexMatch(r"[^\s]+") @ "something",
                FullMatch("#"),
                RegexMatch(r"[^\s]+") @ "other_word",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("marketing_content_generator", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def marketing_content_generator(
    app: Ariadne,
    group: Group,
    source: Source,
    somebody: RegexResult,
    something: RegexResult,
    other_word: RegexResult,
):
    somebody = somebody.result.display.strip()
    something = something.result.display.strip()
    other_word = other_word.result.display.strip()
    content = (
        f"{somebody}{something}是怎么回事呢？"
        f"{somebody}相信大家都很熟悉，但是{somebody}{something}是怎么回事呢，下面就让小编带大家一起了解下吧。\n"
        f"{somebody}{something}，其实就是{somebody}{other_word}，大家可能会很惊讶{somebody}怎么会{something}呢？"
        f"但事实就是这样，小编也感到非常惊讶。\n"
        f"这就是关于{somebody}{something}的事情了，大家有什么想法呢，欢迎在评论区告诉小编一起讨论哦！ "
    )
    await app.send_group_message(group, MessageChain(content), quote=source)
