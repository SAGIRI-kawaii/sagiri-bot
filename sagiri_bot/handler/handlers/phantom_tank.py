import PIL.Image
import numpy as np
from io import BytesIO
from PIL import ImageEnhance

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, ElementMatch, RegexResult, ElementResult, RegexMatch

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()

channel.name("PhantomTank")
channel.author("SAGIRI-kawaii")
channel.description("一个幻影坦克生成器，在群中发送 `幻影 [显示图] [隐藏图]` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("彩色", optional=True) @ "colorful", FullMatch("幻影"),
                RegexMatch(r'[\s]?', optional=True),
                ElementMatch(Image) @ "img1", RegexMatch(r'[\s]?', optional=True), ElementMatch(Image) @ "img2"
            ])
        ],
        decorators=[
            FrequencyLimit.require("phantom_tank", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def phantom_tank(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    colorful: RegexResult,
    img1: ElementResult,
    img2: ElementResult
):
    async with get_running(Adapter).session.get(url=img1.result.url) as resp:
        display_img = PIL.Image.open(BytesIO(await resp.read()))
    async with get_running(Adapter).session.get(url=img2.result.url) as resp:
        hide_img = PIL.Image.open(BytesIO(await resp.read()))
    if colorful.matched:
        msg = MessageChain([Image(data_bytes=await PhantomTank.colorful_tank(display_img, hide_img))])
    else:
        msg = MessageChain([Image(data_bytes=await PhantomTank.make_tank(display_img, hide_img))])
    await app.sendGroupMessage(group, msg, quote=message.getFirst(Source))


class PhantomTank(object):

    @staticmethod
    def get_max_size(a, b):
        return a if a[0] * a[1] >= b[0] * b[1] else b

    @staticmethod
    async def make_tank(im_1: PIL.Image, im_2: PIL.Image) -> bytes:
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
        PIL.Image.fromarray(arr_new).save(bytesIO, format='PNG')
        return bytesIO.getvalue()

    @staticmethod
    async def colorful_tank(
            wimg: PIL.Image.Image,
            bimg: PIL.Image.Image,
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
        PIL.Image.fromarray(colors.astype("uint8")).convert("RGBA").save(bytesIO, format='PNG')

        return bytesIO.getvalue()
