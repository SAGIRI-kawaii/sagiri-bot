import aiohttp
import numpy as np
from io import BytesIO
from PIL import Image as IMG
from PIL import ImageEnhance

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount


saya = Saya.current()
channel = Channel.current()

channel.name("PhantomTank")
channel.author("SAGIRI-kawaii")
channel.description("一个幻影坦克生成器，在群中发送 `幻影 [显示图] [隐藏图]` 即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def phantom_tank(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await PhantomTank.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class PhantomTank(AbstractHandler):
    __name__ = "PhantomTank"
    __description__ = "一个幻影坦克生成器"
    __usage__ = "在群中发送 `幻影 [显示图] [隐藏图]` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        message_text = "".join([plain.text for plain in message.get(Plain)]).strip()
        if message_text == "幻影" or message_text == "彩色幻影":
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            if len(message.get(Image)) != 2:
                return MessageItem(
                    MessageChain.create([Plain(text="非预期图片数！请按照 `显示图 隐藏图` 顺序发送，一共两张图片")]),
                    QuoteSource()
                )
            else:
                display_img = message[Image][0]
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=display_img.url) as resp:
                        display_img = IMG.open(BytesIO(await resp.read()))

                hide_img = message[Image][1]
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=hide_img.url) as resp:
                        hide_img = IMG.open(BytesIO(await resp.read()))

                return await PhantomTank.get_phantom_message(group, member, display_img, hide_img) \
                    if message_text == "幻影" else \
                    await PhantomTank.get_colorful_phantom_message(group, member, display_img, hide_img)
        else:
            return None

    @staticmethod
    @frequency_limit_require_weight_free(2)
    async def get_phantom_message(group: Group, member: Member, display_img: IMG, hide_img: IMG):
        return MessageItem(
            MessageChain.create([Image(data_bytes=await PhantomTank.make_tank(display_img, hide_img))]),
            QuoteSource()
        )

    @staticmethod
    @frequency_limit_require_weight_free(2)
    async def get_colorful_phantom_message(group: Group, member: Member, display_img: IMG, hide_img: IMG):
        return MessageItem(
            MessageChain.create([Image(data_bytes=await PhantomTank.colorful_tank(display_img, hide_img))]),
            QuoteSource()
        )

    @staticmethod
    def get_max_size(a, b):
        return a if a[0] * a[1] >= b[0] * b[1] else b

    @staticmethod
    async def make_tank(im_1: IMG, im_2: IMG) -> bytes:
        im_1 = im_1.convert("L")
        im_2 = im_2.convert("L")
        max_size = PhantomTank.get_max_size(im_1.size, im_2.size)
        if max_size == im_1.size:
            im_2 = im_2.resize(max_size)
        else:
            im_1 = im_1.resize(max_size)
        arr_1 = np.array(im_1, dtype=np.uint8)
        arr_2 = np.array(im_2, dtype=np.uint8)
        arr_1 = 225 - 70 * ((np.max(arr_1) - arr_1) / (np.max(arr_1) - np.min(arr_1)))
        arr_2 = 30 + 70 * ((arr_2 - np.min(arr_2)) / (np.max(arr_2) - np.min(arr_2)))
        arr_alpha = 255 - (arr_1 - arr_2)
        arr_offset = arr_2 * (255 / arr_alpha)
        arr_new = np.dstack([arr_offset, arr_alpha]).astype(np.uint8)
        if arr_new.shape[0] == 3:
            arr_new = (np.transpose(arr_new, (1, 2, 0)) + 1) / 2.0 * 255.0
        bytesIO = BytesIO()
        IMG.fromarray(arr_new).save(bytesIO, format='PNG')
        return bytesIO.getvalue()

    @staticmethod
    async def colorful_tank(
            wimg: IMG.Image,
            bimg: IMG.Image,
            wlight: float = 1.0,
            blight: float = 0.18,
            wcolor: float = 0.5,
            bcolor: float = 0.7,
            chess: bool = False
    ):
        wimg = ImageEnhance.Brightness(wimg).enhance(wlight).convert("RGB")
        bimg = ImageEnhance.Brightness(bimg).enhance(blight).convert("RGB")

        async def get_max_size(a, b):
            return a if a[0] * a[1] >= b[0] * b[1] else b

        max_size = await get_max_size(wimg.size, bimg.size)
        if max_size == wimg.size:
            bimg = bimg.resize(max_size)
        else:
            wimg = wimg.resize(max_size)

        wpix = np.array(wimg).astype("float64")
        bpix = np.array(bimg).astype("float64")

        if chess:
            wpix[::2, ::2] = [255., 255., 255.]
            bpix[1::2, 1::2] = [0., 0., 0.]

        wpix /= 255.
        bpix /= 255.

        wgray = wpix[:, :, 0] * 0.334 + wpix[:, :, 1] * 0.333 + wpix[:, :, 2] * 0.333
        wpix *= wcolor
        wpix[:, :, 0] += wgray * (1. - wcolor)
        wpix[:, :, 1] += wgray * (1. - wcolor)
        wpix[:, :, 2] += wgray * (1. - wcolor)

        bgray = bpix[:, :, 0] * 0.334 + bpix[:, :, 1] * 0.333 + bpix[:, :, 2] * 0.333
        bpix *= bcolor
        bpix[:, :, 0] += bgray * (1. - bcolor)
        bpix[:, :, 1] += bgray * (1. - bcolor)
        bpix[:, :, 2] += bgray * (1. - bcolor)

        d = 1. - wpix + bpix

        d[:, :, 0] = d[:, :, 1] = d[:, :, 2] = d[:, :, 0] * 0.222 + d[:, :, 1] * 0.707 + d[:, :, 2] * 0.071

        p = np.where(d != 0, bpix / d * 255., 255.)
        a = d[:, :, 0] * 255.

        colors = np.zeros((p.shape[0], p.shape[1], 4))
        colors[:, :, :3] = p
        colors[:, :, -1] = a

        colors[colors > 255] = 255

        bytesIO = BytesIO()
        IMG.fromarray(colors.astype("uint8")).convert("RGBA").save(bytesIO, format='PNG')

        return bytesIO.getvalue()
