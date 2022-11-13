import json
import random
from pathlib import Path

from graia.saya import Saya, Channel
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

saya = Saya.current()
channel = Channel.current()

channel.name("CPGenerator")
channel.author("SAGIRI-kawaii")
channel.description("生成CP文的插件，在群中发送 `/cp {攻名字} {受名字}` 即可")

with open(Path(__file__).parent / "cp_data.json", "r", encoding="utf-8") as r:
    cp_data = json.loads(r.read())


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r"[^\s]+") @ "attack",
                RegexMatch(r"[^\s]+") @ "defence",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("cp_generator", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def cp_generator(app: Ariadne, group: Group, source: Source, attack: RegexResult, defence: RegexResult):
    attack = attack.result.display
    defence = defence.result.display
    template = random.choice(cp_data["data"])
    content = template.replace("<攻>", attack).replace("<受>", defence)
    await app.send_group_message(group, MessageChain(content), quote=source)
