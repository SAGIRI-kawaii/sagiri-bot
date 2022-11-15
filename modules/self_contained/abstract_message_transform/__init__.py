import re
import json
from pathlib import Path

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("AbstractMessageTransformer")
channel.author("SAGIRI-kawaii")
channel.description("一个普通话转抽象话的插件，在群中发送 `/抽象 文字` 即可")

pinyin = json.loads((Path(__file__).parent / "pinyin.json").read_text(encoding="utf-8"))
emoji = json.loads((Path(__file__).parent / "emoji.json").read_text(encoding="utf-8"))


def get_pinyin(char: str):
    return pinyin[char] if char in pinyin else "None"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r".*").flags(re.DOTALL).help("要转抽象的内容") @ "content",
            ])
        ],
        decorators=[
            Distribute.distribute(),
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
