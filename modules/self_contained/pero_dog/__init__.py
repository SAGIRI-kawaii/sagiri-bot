import json
import random
from pathlib import Path

from graia.saya import Channel
from graia.ariadne.app import Ariadne
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
channel.name("PeroDog")
channel.author("SAGIRI-kawaii")
channel.description("一个获取舔狗日记的插件，在群中发送 `舔` 即可")

pero_dog_contents = json.loads((Path(__file__).parent / "pero_content.json").read_text(encoding="utf-8"))["data"]


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("pero_dog", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def pero_dog(app: Ariadne, group: Group):
    await app.send_group_message(group, MessageChain(random.choice(pero_dog_contents).replace("*", "")))
