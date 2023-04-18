import aiohttp
import asyncio

from creart import create
from graia.saya import Channel
from graia.ariadne import Ariadne
from graia.broadcast import Broadcast
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Source, File, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from .utils import gen_watermark
from shared.utils.waiter import ElementWaiter
from shared.models.config import GlobalConfig
from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()
channel.name("CameraWatermark")
channel.author("SAGIRI-kawaii")
channel.description("一个可以根据exif信息添加相机水印的插件，在群中发送 `/相机水印 + 图片（必须原图）` 即可")

config = create(GlobalConfig)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("camera_watermark", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def camera_watermark(app: Ariadne, group: Group, member: Member, source: Source):
    try:
        await app.send_message(group, MessageChain("请在30s内发送要处理的图片原图（文件形式）"), quote=source)
        file = await asyncio.wait_for(InterruptControl(create(Broadcast)).wait(ElementWaiter(group, member, File)), 30)
        if not file:
            return await app.send_group_message(
                group, MessageChain("未检测到文件，请重新发送，进程退出"), quote=source
            )
    except asyncio.TimeoutError:
        return await app.send_group_message(
            group, MessageChain("文件等待超时，进程退出"), quote=source
        )
    file = await app.get_file_info(group, file.id, with_download_info=True)
    async with aiohttp.ClientSession() as session:
        async with session.get(file.download_info.url) as resp:
            stream = await resp.read()
    await app.send_group_message(group, MessageChain("已收到图片，正在处理..."), quote=source)
    res = await gen_watermark(stream)
    if isinstance(res, str):
        return await app.send_group_message(group, MessageChain(res))
    await app.send_group_message(group, MessageChain(Image(data_bytes=res)))
