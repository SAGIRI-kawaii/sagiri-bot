import json
import random
from pathlib import Path

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()
channel.name("RandomCharacter")
channel.author("SAGIRI-kawaii")
channel.description("随机生成人设插件，在群中发送 `随机人设` 即可")

character = json.loads((Path(__file__).parent / "character.json").read_text(encoding="utf-8"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("random_character", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def random_character(app: Ariadne, group: Group, source: Source):
    await app.send_group_message(
        group,
        MessageChain(
            "\n".join([
                f"{k}：{random.choice(character[k])}"
                for k in character.keys()
            ])
        ),
        quote=source,
    )
