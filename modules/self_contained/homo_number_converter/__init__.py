from graia.saya import Channel
from graia.ariadne import Ariadne
from graia.ariadne.message.element import Source
from graia.saya.builtins.broadcast import ListenerSchema
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, RegexResult

from .utils import get_expression
from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("Example")
channel.author("SAGIRI-kawaii")
channel.description("这是一个示例插件")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r"-?\d+\.?(\d+)?") @ "real",
                RegexMatch(r"(\+|-)\d+\.?(\d+)?i", optional=True) @ "imaginary"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("homo_number_converter", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ]
    )
)
async def homo_number_converter(app: Ariadne, group: Group, real: RegexResult, imaginary: RegexResult, source: Source):
    imaginary_expression = get_expression(imaginary.result.display.strip()[:-1]) if imaginary.matched else None
    left_expression = f"{real.result.display.strip()}"
    left_expression += f"{imaginary.result.display.strip()}=" if imaginary.matched else "="
    await app.send_group_message(
        group,
        left_expression +
        get_expression(real.result.display.strip()) +
        (f"+({imaginary_expression})i" if imaginary_expression else ""),
        quote=source
    )
