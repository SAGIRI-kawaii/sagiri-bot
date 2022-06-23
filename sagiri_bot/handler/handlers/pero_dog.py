import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.parser.twilight import FullMatch
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from statics.pero_dog_contents import pero_dog_contents
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("PeroDog")
channel.author("SAGIRI-kawaii")
channel.description("一个获取舔狗日记的插件，在群中发送 `舔` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("舔")])],
        decorators=[
            FrequencyLimit.require("pero_dog", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def pero_dog(app: Ariadne, group: Group):
    await app.sendGroupMessage(group, MessageChain(random.choice(pero_dog_contents).replace('*', '')))
