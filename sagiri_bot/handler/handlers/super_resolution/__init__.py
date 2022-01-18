import time
import asyncio
import numpy as np
from io import BytesIO
from pathlib import Path
from typing import Optional
from PIL import Image as IMG
from threading import Semaphore

try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    enable = True
except ImportError:
    enable = False

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import FullMatch, ElementMatch

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
loop = bcc.loop

channel.name("SuperResolution")
channel.author("SAGIRI-kawaii")
channel.description("一个图片超分插件，在群中发送 `/超分 图片` 即可")

upsampler = RealESRGANer(
    scale=4,
    model_path=str(Path(__file__).parent.joinpath("RealESRGAN_x4plus_anime_6B.pth")),
    model=RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=6,
        num_grow_ch=32,
        scale=4,
    ),
    tile=0,
    tile_pad=10,
    pre_pad=0,
    half=False,
) if enable else None

max_size = 2073600
mutex = Semaphore(1)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [
                        FullMatch("/超分")
                    ],
                    {
                        "resize": FullMatch("-resize", optional=True),
                        "enter": FullMatch("\n", optional=True),
                        "image": ElementMatch(Image, optional=True)
                    }
                )
            )
        ]
    )
)
async def super_resolution(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    image: ElementMatch,
    resize: FullMatch
):
    if result := await SuperResolution.handle(app, message, group, member, image, resize):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class SuperResolution(AbstractHandler):
    __name__ = "SuperResolution"
    __description__ = "一个图片超分插件"
    __usage__ = "在群中发送 `/超分 图片` 即可"

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
        image: ElementMatch,
        resize: FullMatch
    ) -> Optional[MessageItem]:

        @Waiter.create_using_function(listening_events=[GroupMessage])
        async def image_waiter(
            waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
        ):
            if waiter_group.id == group.id and waiter_member.id == member.id:
                if waiter_message.has(Image):
                    return await waiter_message.getFirst(Image).get_bytes()
                else:
                    return False
        if not enable:
            return MessageItem(MessageChain.create([Plain(text="功能未开启！")]), QuoteSource())
        if image.matched:
            image_data = await image.result.get_bytes()
        else:
            try:
                await app.sendMessage(
                    group, MessageChain.create("请在30s内发送要处理的图片"), quote=message[Source][0]
                )
                image_data = await asyncio.wait_for(inc.wait(image_waiter), 30)
                if not image_data:
                    return MessageItem(MessageChain.create([Plain(text="未检测到图片，请重新发送，进程退出")]), QuoteSource())
            except asyncio.TimeoutError:
                return MessageItem(MessageChain.create([Plain(text="图片等待超时，进程退出")]), QuoteSource())
        mutex.acquire()
        if SuperResolution.processing:
            mutex.release()
            return MessageItem(MessageChain.create([Plain(text="有任务正在处理中，请稍后重试")]), QuoteSource())
        SuperResolution.processing = True
        mutex.release()
        await app.sendMessage(
            group,
            MessageChain.create([Plain(text="已收到图片，启动处理进程")]),
            quote=message[Source][0]
        )
        try:
            return await SuperResolution.super_resolution(image_data, resize.matched)
        except RuntimeError as e:
            mutex.acquire()
            SuperResolution.processing = False
            mutex.release()
            return MessageItem(MessageChain.create([Plain(text=str(e))]), QuoteSource())

    @staticmethod
    async def super_resolution(image_data: bytes, resize: bool = False) -> MessageItem:
        start = time.time()
        image = IMG.open(BytesIO(image_data))
        image_size = image.size[0] * image.size[1]
        if image_size > max_size:
            if not resize:
                return MessageItem(
                    MessageChain.create([
                        Plain(text="图片尺寸过大！请发送1080p以内即像素数小于 1920×1080=2073600的照片！\n"),
                        Plain(text=f"此图片尺寸为：{image.size[0]}×{image.size[1]}={image_size}！")
                    ]),
                    QuoteSource()
                )
            length = 1
            for b in str(max_size / image_size).split('.')[1]:
                if b == '0':
                    length += 1
                else:
                    break
            magnification = round(max_size / image_size, length + 1)
            image = image.resize((round(image.size[0] * magnification), round(image.size[1] * magnification)))
        image_array: np.ndarray = image.__array__()
        output, _ = await loop.run_in_executor(None, upsampler.enhance, image_array, 2)
        result = BytesIO()
        img = IMG.fromarray(output)
        img.save(result, format='PNG')  # format: PNG / JPEG
        end = time.time()
        use_time = round(end - start, 2)
        mutex.acquire()
        SuperResolution.processing = False
        mutex.release()
        return MessageItem(
            MessageChain.create([
                Plain(text=f"超分完成！处理用时：{use_time}s\n"),
                Plain(text=f"由于像素过大，图片已进行缩放，结果可能不如原图片清晰\n" if resize else ""),
                Image(data_bytes=result.getvalue())
            ]),
            QuoteSource()
        )
