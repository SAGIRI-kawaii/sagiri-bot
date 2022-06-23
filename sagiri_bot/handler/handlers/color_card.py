import os
import asyncio
import PIL.Image
from enum import Enum
from io import BytesIO
from pathlib import Path
from PIL import ImageDraw
from typing import Union, Tuple

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, GroupMessage, Member
from graia.ariadne.message.element import Image, Source, Plain, At, Quote
from graia.ariadne.message.parser.twilight import ElementMatch, RegexMatch, ElementResult, RegexResult, ArgumentMatch

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()

channel.name("ColorCard")
channel.author("SAGIRI-kawaii")
channel.description("一个获取图片色卡的插件，在群中发送 `/色卡 -s={size} -m={mode} -t {图片/@成员/qq号/回复有图片的消息}` 即可，发送 `/色卡 -h` 查看帮助")

loop = AppCore.get_core_instance().get_loop()
bcc = saya.broadcast
inc = InterruptControl(bcc)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                ElementMatch(At, optional=True),
                RegexMatch(r"/?色卡"),
                ArgumentMatch("-h", "-help", optional=True, action="store_true") @ "help",
                RegexMatch(r"-(s|size)=[0-9]+", optional=True) @ "size",
                RegexMatch(r"-(m|mode)=\w+", optional=True) @ "mode",
                RegexMatch(r"-(t|text)", optional=True) @ "text",
                RegexMatch(r"[\n\r]?", optional=True),
                ElementMatch(Image, optional=True) @ "image",
                ElementMatch(At, optional=True) @ "at",
                RegexMatch(r"[1-9][0-9]+", optional=True) @ "qq",
                RegexMatch(r"[\n\r]?", optional=True)
            ])
        ],
        decorators=[
            FrequencyLimit.require("color_card", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def color_card(
    app: Ariadne,
    group: Group,
    member: Member,
    message: MessageChain,
    help: RegexResult,
    size: RegexResult,
    mode: RegexResult,
    text: RegexResult,
    image: ElementResult,
    at: ElementResult,
    qq: RegexResult
):
    source = message.getFirst(Source)
    if help.matched:
        await app.sendGroupMessage(
            group,
            MessageChain(
                "ColorCard色卡插件\n"
                "在群中发送 `/色卡 {图片/@成员/qq号/回复有图片的消息}` 即可\n"
                "可选参数：\n"
                "   -s/-size：色卡颜色个数，在群中发送 `/色卡 -s={size} {图片/@成员/qq号/回复有图片的消息}` 即可，默认值为5\n"
                "   -m/-mode：色卡形式，在群中发送 `/色卡 -s={size} {图片/@成员/qq号/回复有图片的消息}` 即可，默认值为center，可选值及说明如下：\n"
                "       pure：纯颜色\n"
                "       below：在下方添加方形色块\n"
                "       center：在图片中央添加圆形色块（自适应，若图片长>宽则为center_horizon，反之则为center_vertical）\n"
                "       center_horizon：在图片中央水平添加圆形色块\n"
                "       center_vertical：在图片中央垂直添加圆形色块\n"
                "   -t/-text：是否在下方附加色块RGB即十六进制值文本，在群中发送 `/色卡 -t {图片/@成员/qq号/回复有图片的消息}` 即可\n"
                "上述参数可同步使用，并按照 -s、-m、-t的顺序添加，如 `/色卡 -s=10 -m=pure -t {图片/@成员/qq号/回复有图片的消息}`"
            ),
            quote=source
        )
        return
    size = int(size.result.asDisplay().split('=')[1].strip()) if size.matched else 5
    if size <= 0:
        await app.sendGroupMessage(group, MessageChain(f"蛤？size为{size}我还给你什么色卡阿，爪巴巴！"), quote=source)
        return
    elif size > 30:
        await app.sendGroupMessage(group, MessageChain(f"太多了啦，要溢出了！"), quote=source)
        return
    if mode.matched:
        mode = mode.result.asDisplay().split('=')[1].strip().lower()
        if mode == "center_vertical":
            mode = CardType.CENTER_VERTICAL
        elif mode == "center_horizon":
            mode = CardType.CENTER_HORIZON
        elif mode == "center":
            mode = CardType.CENTER
        elif mode == "pure":
            mode = CardType.PURE
        elif mode == "below":
            mode = CardType.BELOW_BLOCK
        else:
            await app.sendGroupMessage(
                group,
                MessageChain("mode参数错误！合法的参数如下：center_vertical、center_horizon、center、pure、below"),
                quote=source
            )
            return
    else:
        mode = CardType.CENTER

    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def image_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            if waiter_message.has(Image):
                return await waiter_message.getFirst(Image).get_bytes()
            else:
                return False

    if image.matched:
        image_bytes = await image.result.get_bytes()
    elif at.matched or qq.matched:
        url = f'http://q1.qlogo.cn/g?b=qq&nk={at.result.target if at.matched else qq.result.asDisplay().strip()}&s=640'
        async with get_running(Adapter).session.get(url=url) as resp:
            image_bytes = await resp.read()
    else:
        try:
            if message.getFirst(Quote) and (await app.getMessageFromId(message.getFirst(Quote).id)).messageChain.get(Image):
                image_bytes = await (await app.getMessageFromId(message.getFirst(Quote).id)).messageChain.getFirst(Image).get_bytes()
            else:
                raise AttributeError()
        except (IndexError, AttributeError):
            try:
                await app.sendMessage(group, MessageChain("请在30s内发送要处理的图片"), quote=source)
                image_bytes = await asyncio.wait_for(inc.wait(image_waiter), 30)
                if not image_bytes:
                    await app.sendGroupMessage(group, MessageChain("未检测到图片，请重新发送，进程退出"), quote=source)
                    return
            except asyncio.TimeoutError:
                await app.sendGroupMessage(group, MessageChain("图片等待超时，进程退出"), quote=source)
                return

    result = await loop.run_in_executor(None, draw, image_bytes, mode, size)
    bytes_io = BytesIO()
    result[0].save(bytes_io, "PNG")
    if text.matched:
        await app.sendGroupMessage(
            group,
            MessageChain([
                Image(data_bytes=bytes_io.getvalue()),
                Plain("\n"),
                Plain("\n".join([f"rgb{str(i).ljust(15, ' ')} #{''.join(hex(i[j]).upper()[2:] for j in range(3))}" for i in result[1]]))
            ]),
            quote=source
        )
    else:
        await app.sendGroupMessage(group, MessageChain([Image(data_bytes=bytes_io.getvalue())]), quote=source)


class CardType(Enum):
    PURE = "纯色卡"
    BELOW_BLOCK = "在下方添加方块"
    BELOW_LINE = "在下方添加横行"
    CENTER = "图片中央垂直添加圆形色块(自动更改)"
    CENTER_HORIZON = "图片中央水平添加圆形色块"
    CENTER_VERTICAL = "图片中央垂直添加圆形色块"


def draw_ellipse(image, bounds, width=1, antialias=4):
    mask = PIL.Image.new(
        size=[int(dim * antialias) for dim in image.size],
        mode='L', color='black'
    )
    canvas = ImageDraw.Draw(mask)

    for offset, fill in (width / -2.0, 'black'), (width / 2.0, 'white'):
        left, top = [(value + offset) * antialias for value in bounds[:2]]
        right, bottom = [(value - offset) * antialias for value in bounds[2:]]
        canvas.ellipse([left, top, right, bottom], fill=fill)

    mask = mask.resize(image.size, PIL.Image.LANCZOS)

    image.putalpha(mask)


def get_circle_color(
    color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]],
    size: Tuple[int, int],
    border: bool = True,
    border_color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]] = "white"
) -> PIL.Image:
    border_width = int(min(size[0], size[1]) * 0.04) if border else 0
    canvas_back = None
    if border:
        canvas_back = PIL.Image.new("RGBA", size, border_color)
        r1 = min(size[0], size[1])
        size = (size[0] - 2 * border_width, size[1] - 2 * border_width)
        draw_ellipse(canvas_back, [0, 0, r1 - 2, r1 - 2], width=1)
    canvas = PIL.Image.new("RGBA", size, color)
    r2 = min(size[0], size[1])
    if size[0] != size[1]:
        canvas = canvas.resize((r2, r2), PIL.Image.ANTIALIAS)
    ellipse_box = [0, 0, r2 - 2, r2 - 2]
    draw_ellipse(canvas, ellipse_box, width=1)
    if border:
        result = PIL.Image.new("RGBA", (r1, r1))
        result = PIL.Image.alpha_composite(result, canvas_back)
        canvas_fit = PIL.Image.new("RGBA", (r1, r1))
        canvas_fit.paste(canvas, (int((r1 - r2) / 2), int((r1 - r2) / 2)))
        result = PIL.Image.alpha_composite(result, canvas_fit)
        return result
    return canvas


def get_dominant_colors(image: PIL.Image, size: int = 5):
    result = image.convert("P", palette=PIL.Image.ADAPTIVE, colors=size)

    palette = result.getpalette()
    color_counts = sorted(result.getcolors(), reverse=True)
    colors = list()

    for i in range(size):
        palette_index = color_counts[i][1]
        dominant_color = palette[palette_index * 3: palette_index * 3 + 3]
        colors.append(tuple(dominant_color))

    return colors


def draw(
    image: Union[str, bytes, Path],
    card_type: CardType = CardType.CENTER,
    color_size: int = 5,
    show: bool = False,
    resize: bool = False,
):
    if isinstance(image, bytes):
        image = PIL.Image.open(BytesIO(image))
    elif not os.path.exists(image):
        raise ValueError(f"{image} is not exist!")
    else:
        image = PIL.Image.open(image)
    if resize:
        image = image.resize((100, 100))
    image = image.convert("RGBA")
    colors = get_dominant_colors(image, color_size)
    if card_type == CardType.CENTER:
        card_type = CardType.CENTER_HORIZON if image.size[0] > image.size[1] else CardType.CENTER_VERTICAL
    if card_type == CardType.PURE:
        height = 100
        width = 100 * len(colors)
        canvas = PIL.Image.new("RGBA", (width, height), (0, 0, 0, 0))
        for i in range(len(colors)):
            block = PIL.Image.new("RGB", (100, 100), colors[i])
            canvas.paste(block, (i * 100, 0))
    elif resize:
        raise TypeError("The resize option cannot be used in drawing modes other than CardType.PURE!")
    elif card_type == CardType.BELOW_BLOCK:
        width, height = image.size
        block_width = int(width / color_size)
        canvas = PIL.Image.new("RGBA", (width, height + block_width), "white")
        canvas.paste(image, (0, 0))
        for i in range(len(colors)):
            block = PIL.Image.new("RGBA", (block_width, block_width), colors[i])
            canvas.paste(block, (i * block_width, height))
            if i == len(colors) - 1:
                canvas.paste(block, ((i + 1) * block_width, height))
    elif card_type == CardType.CENTER_HORIZON or card_type == CardType.CENTER_VERTICAL:
        width, height = image.size
        canvas = PIL.Image.new("RGBA", image.size)
        draw_size = int(width * 0.7) if card_type == CardType.CENTER_HORIZON else int(height * 0.7)
        padding = int(width * 0.02) if card_type == CardType.CENTER_HORIZON else int(height * 0.02)
        block_size = int((draw_size - (color_size - 1) * padding) / color_size)
        stable_x = int((height if card_type == CardType.CENTER_HORIZON else width) / 2 - block_size / 2)
        for i in range(len(colors)):
            block = get_circle_color(colors[i], (block_size, block_size))
            if card_type == CardType.CENTER_HORIZON:
                canvas.paste(block, (int(width * 0.15) + i * (block_size + padding), stable_x))
            else:
                canvas.paste(block, (stable_x, int(height * 0.15) + i * (block_size + padding)))
        canvas = PIL.Image.alpha_composite(image, canvas)
    if show:
        canvas.show()
    return canvas, colors


# draw(image_path, CardType.CENTER, 5, resize=False, show=True)

