from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from sagiri_bot.internal_utils import get_command
from statics.abstract_message_transformer_data import pinyin, emoji
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)


def get_pinyin(char: str):
    return pinyin[char] if char in pinyin else "None"


saya = Saya.current()
channel = Channel.current()

channel.name("AbstractMessageTransformer")
channel.author("SAGIRI-kawaii")
channel.description("一个普通话转抽象话的插件，在群中发送 `/抽象 文字` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    get_command(__file__, channel.module),
                    RegexMatch(r".*").help("要转抽象的内容") @ "content",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("abstract_message_transformer", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def abstract_message_transformer(
    app: Ariadne, group: Group, source: Source, content: RegexResult
):
    result = ""
    content = content.result.display
    length = len(content)
    index = 0
    while index < length:
        if (
            index < length - 1
            and (get_pinyin(content[index]) + get_pinyin(content[index + 1])) in emoji
        ):
            result += emoji[get_pinyin(content[index]) + get_pinyin(content[index + 1])]
            index += 1
        elif get_pinyin(content[index]) in emoji:
            result += emoji[get_pinyin(content[index])]
        else:
            result += content[index]
        index += 1
    await app.send_group_message(group, MessageChain(result), quote=source)
