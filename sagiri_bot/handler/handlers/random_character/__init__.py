import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from statics.character_dict import character_dict
from sagiri_bot.internal_utils import get_command
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("RandomCharacter")
channel.author("SAGIRI-kawaii")
channel.description("随机生成人设插件，在群中发送 `随机人设` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            FrequencyLimit.require("random_character", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def random_character(app: Ariadne, group: Group, source: Source):
    await app.send_group_message(
        group,
        MessageChain("\n".join([f"{k}：{random.choice(character_dict[k])}" for k in character_dict.keys()])),
        quote=source
    )
