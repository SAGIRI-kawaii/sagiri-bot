import random
from pathlib import Path

from graiax import silkcoder
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Voice
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

channel.name("KugimiyaVoice")
channel.author("SAGIRI-kawaii")
channel.description("一个钉宫语音包插件，发送 `来点钉宫` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("kugimiya_voice", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def kugimiya_voice(app: Ariadne, group: Group):
    base_path = Path.cwd() / "resources" / "voice" / "kugimiya"
    path = base_path / random.sample(list(base_path.glob("*.mp3")), 1)[0]
    print(path)
    await app.send_group_message(
        group,
        MessageChain(Voice(data_bytes=await silkcoder.async_encode(path, rate=24000))),
    )
