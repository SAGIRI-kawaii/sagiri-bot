from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, RegexResult

from utils.text_engine.adapter import GraiaAdapter
from utils.text_engine.text_engine import TextEngine
from .query_resource import get_resource_type_list, query_resource, init, check_resource_exists
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
loop = bcc.loop

channel.name("GenshinResourcePoints")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个获取原神资源的插件\n"
    "在群中发送 `{resource_name} 在哪里? | 哪里?有 {resource_name}` 即可查看资源地图\n"
    "在群中发送 `原神资源列表` 即可查看资源列表"
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("原神"), RegexMatch(r"哪里?有", optional=True),
                RegexMatch(r"[^\s]+") @ "resource_name", RegexMatch(r"在哪里?")
            ])
        ],
        decorators=[
            FrequencyLimit.require("genshin_resource_points", 4),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def genshin_resource_points(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    resource_name: RegexResult
):
    resource_name = resource_name.result.asDisplay().strip()
    if check_resource_exists(resource_name):
        await get_resource_list()
        await app.sendGroupMessage(group, MessageChain("正在生成位置...."))
        await app.sendGroupMessage(group, await query_resource(resource_name), quote=message.getFirst(Source))
    else:
        await app.sendGroupMessage(
            group,
            MessageChain(f"未查找到 {resource_name} 资源，可通过 “原神资源列表” 获取全部资源名称.."),
            quote=message.getFirst(Source)
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("原神资源列表")])],
        decorators=[
            FrequencyLimit.require("genshin_resource_point_list", 3),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def genshin_resource_point_list(app: Ariadne, group: Group):
    await app.sendMessage(group, await get_resource_list())


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def resource_init():
    await init()


async def get_resource_list() -> MessageChain:
    content = get_resource_type_list()
    return MessageChain([Image(data_bytes=TextEngine([GraiaAdapter(MessageChain(content))], min_width=4096).draw())])
