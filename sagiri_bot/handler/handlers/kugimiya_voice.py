import os
import random
from graiax import silkcoder

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Voice
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.parser.twilight import FullMatch
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("KugimiyaVoice")
channel.author("SAGIRI-kawaii")
channel.description("一个钉宫语音包插件，发送 `来点钉宫` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("来点钉宫")])],
        decorators=[
            FrequencyLimit.require("kugimiya_voice", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def kugimiya_voice(app: Ariadne, group: Group):
    base_path = f"{os.getcwd()}/statics/voice/kugimiya/"
    path = base_path + random.sample(os.listdir(base_path), 1)[0]
    await app.sendGroupMessage(group, MessageChain([Voice(data_bytes=await silkcoder.async_encode(path, rate=24000))]))
