import asyncio
from datetime import datetime

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.parser.twilight import UnionMatch, RegexMatch, ElementMatch, ElementResult
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Source, Plain, At, Image, Forward, ForwardNode
from graia.ariadne.event.message import Group, Member, GroupMessage

from .baidu import baidu_search
from .google import google_search
from .ascii2d import ascii2d_search
from .ehentai import ehentai_search
from .saucenao import saucenao_search
from sagiri_bot.utils import group_setting
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

channel.name("ImageSearch")
channel.author("SAGIRI-kawaii")
channel.description("一个可以以图搜图的插件，在群中发送 `搜图` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）")

core = AppCore.get_core_instance()
bcc = core.get_bcc()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else None
SAUCENAO_API_KEY = config.functions.get("saucenao_api_key", None)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("搜图", "识图", "以图搜图"),
                RegexMatch(r"[\s]+", optional=True),
                ElementMatch(Image, optional=True) @ "image"
            ])
        ],
        decorators=[
            FrequencyLimit.require("image_searcher", 3),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def image_searcher(app: Ariadne, message: MessageChain, group: Group, member: Member, image: ElementResult):

    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def image_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            if waiter_message.has(Image):
                return waiter_message.getFirst(Image).url
            else:
                return False
    if not await group_setting.get_setting(group, Setting.img_search):
        return await app.sendGroupMessage(group, MessageChain("搜图功能已经关闭了，请联系管理员哦~"))
    if not image.matched:
        try:
            await app.sendMessage(
                group, MessageChain("请在30s内发送要处理的图片"), quote=message.getFirst(Source)
            )
            image = await asyncio.wait_for(inc.wait(image_waiter), 30)
            if not image:
                return await app.sendGroupMessage(
                    group, MessageChain("未检测到图片，请重新发送，进程退出"), quote=message.getFirst(Source)
                )
        except asyncio.TimeoutError:
            return await app.sendGroupMessage(
                group, MessageChain("图片等待超时，进程退出"), quote=message.getFirst(Source)
            )
    else:
        image = image.result.url
    await app.sendGroupMessage(group, MessageChain("已收到图片，正在进行搜索..."), quote=message.getFirst(Source))
    tasks = [
        asyncio.create_task(saucenao_search(SAUCENAO_API_KEY, proxy, url=image)),
        asyncio.create_task(ascii2d_search(proxy, url=image)),
        asyncio.create_task(ehentai_search(proxy, url=image)),
        asyncio.create_task(google_search(proxy, url=image)),
        asyncio.create_task(baidu_search(url=image))
    ]
    msgs = await asyncio.gather(*tasks)
    await app.sendGroupMessage(group, MessageChain([
        Forward([
            ForwardNode(
                senderId=config.bot_qq,
                time=datetime.now(),
                senderName="SAGIRI BOT",
                messageChain=msg,
            ) for msg in msgs
        ])
    ]))
