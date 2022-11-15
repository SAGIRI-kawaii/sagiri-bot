import json
import random
from pathlib import Path

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult

from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()

channel.name("Joke")
channel.author("SAGIRI-kawaii")
channel.description("一个生成笑话的插件，在群中发送 `来点{keyword|法国|苏联|美国}笑话`")

jokes = json.loads((Path(__file__).parent / "jokes.json").read_text(encoding="utf-8"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("来点"), RegexMatch(r"[^\s]+") @ "keyword", FullMatch("笑话")])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("joke", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def joke(app: Ariadne, group: Group, keyword: RegexResult):
    keyword = keyword.result.display
    await app.send_group_message(
        group,
        MessageChain(
            random.choice(jokes[keyword] if keyword in jokes.keys() else jokes["jokes"]).replace("%name%", keyword)
        )
    )

