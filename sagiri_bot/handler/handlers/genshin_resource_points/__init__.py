from typing import Optional

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle

from sagiri_bot.utils import MessageChainUtils
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free
from .query_resource import get_resource_type_list, query_resource, init, check_resource_exists


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
            Twilight(
                Sparkle(
                    [FullMatch("原神"), RegexMatch(r"哪里?有", optional=True)],
                    {
                        "resource_name": RegexMatch(r".+"),
                        "where": RegexMatch(r"在哪里?")
                    }
                )
            )
        ]
    )
)
async def genshin_resource_points(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    resource_name: RegexMatch
):
    if result := await GenshinResourcePoints.handle(app, message, group, member, resource_name):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([FullMatch("原神资源列表")]))]
    )
)
async def genshin_resource_point_list(app: Ariadne, group: Group):
    await app.sendMessage(group, await GenshinResourcePoints.get_resource_list())


class GenshinResourcePoints(AbstractHandler):
    __name__ = "GenshinResourcePoints"
    __description__ = "一个获取原神资源的插件"
    __usage__ = "在群中发送 `{resource_name} 在哪里? | 哪里?有 {resource_name}` 即可查看资源地图\n" \
                "在群中发送 `原神资源列表` 即可查看资源列表"

    processing = False

    @staticmethod
    @switch()
    @blacklist()
    @frequency_limit_require_weight_free(4)
    async def handle(
        app: Ariadne,
        message: MessageChain,
        group: Group,
        member: Member,
        resource_name: RegexMatch
    ) -> Optional[MessageItem]:
        resource_name = resource_name.result.asDisplay().strip()
        if check_resource_exists(resource_name):
            await GenshinResourcePoints.get_resource_list()
            await app.sendMessage(group, MessageChain.create([Plain(text="正在生成位置....")]))
            return MessageItem(await query_resource(resource_name), QuoteSource())
        else:
            return MessageItem(
                MessageChain.create([Plain(text=f"未查找到 {resource_name} 资源，可通过 “原神资源列表” 获取全部资源名称..")]),
                QuoteSource()
            )

    @staticmethod
    async def get_resource_list():
        content = get_resource_type_list()
        return await MessageChainUtils.messagechain_to_img(MessageChain.create([Plain(text=content)]))
