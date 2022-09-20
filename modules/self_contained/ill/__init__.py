import json
import random
from pathlib import Path

from graia.saya import Channel
from graia.ariadne import Ariadne
from graia.ariadne.message.element import At
from graia.ariadne.model import Group, Member
from graia.ariadne.message.parser.twilight import (
    Twilight,
    ElementMatch,
    ParamMatch,
    ElementResult,
    RegexResult,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast import ListenerSchema

from shared.utils.module_related import get_command
from shared.utils.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl, Distribute

channel = Channel.current()

with Path(Path(__file__).parent, "ill_templates.json").open("r", encoding="UTF-8") as f:
    TEMPLATES = json.loads(f.read())["data"]


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ElementMatch(At, optional=True) @ "at",
                ParamMatch(optional=True) @ "text",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("ill", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def ill(app: Ariadne, group: Group, member: Member, at: ElementResult, text: RegexResult):
    if at.matched:
        _target = at.result.target
        if _target_member := await app.get_member(group, _target):
            target = _target_member.name
        else:
            target = _target
    elif text.matched:
        target = text.result.display.strip()
    else:
        target = member.name
    await app.send_group_message(group, MessageChain(random.choice(TEMPLATES).format(target=target)),)
