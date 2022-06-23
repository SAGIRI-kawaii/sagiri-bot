import os
import shlex
import imageio
from io import BytesIO
from PIL import Image as IMG
from datetime import datetime
from PIL import ImageDraw, ImageFont
from typing import Union, List, Tuple
from PIL.ImageFont import FreeTypeFont

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, UnionMatch, RegexResult

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("Memes")
channel.author("SAGIRI-kawaii")
channel.description("一个生成趣味表情包的插件")

core = AppCore.get_core_instance()
config = core.get_config()

FONT_BASE_PATH = f"{os.getcwd()}/statics/fonts/"
IMAGE_BASE_PATH = f"{os.getcwd()}/statics/memes/"
THUMB_BASE_PATH = f"{os.getcwd()}/statics/memes/"
DEFAULT_FONT = 'SourceHanSansSC-Regular.otf'
OVER_LENGTH_MSG = '文字长度过长，请适当缩减'
BREAK_LINE_MSG = '文字长度过长，请手动换行或适当缩减'


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch(
                    "nokia", "鲁迅说", "王境泽", "喜报", "记仇", "狂爱", "狂粉", "低语", "别说了", "一巴掌", "为所欲为",
                    "馋身子", "切格瓦拉", "谁反对", "连连看", "压力大爷", "你好骚啊", "食屎啦你", "五年", "滚屏"
                ) @ "prefix",
                RegexMatch(r"[\s\S]+") @ "content"
            ])
        ],
        decorators=[
            FrequencyLimit.require("memes", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def memes(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    prefix: RegexResult,
    content: RegexResult
):
    prefix = prefix.result.asDisplay().strip()
    content = [content.result.asDisplay()]
    result = None
    if prefix == "nokia":
        result = await Memes.make_nokia(content)
    elif prefix == "鲁迅说":
        result = await Memes.make_luxunsay(content)
    elif prefix == "喜报":
        result = await Memes.make_goodnews(content)
    elif prefix == "记仇":
        result = await Memes.make_jichou(content)
    elif prefix in ("狂爱", "狂粉"):
        result = await Memes.make_fanatic(content)
    elif prefix == "低语":
        result = await Memes.make_diyu(content)
    elif prefix == "别说了":
        result = await Memes.make_shutup(content)
    elif prefix == "一巴掌":
        result = await Memes.make_slap(content)
    elif prefix == "滚屏":
        result = await Memes.make_scroll(content)
    else:
        content = shlex.split(content[0])
        for key in gif_subtitle_memes.keys():
            if prefix in gif_subtitle_memes[key]["aliases"]:
                if len(content) != len(gif_subtitle_memes[key]["pieces"]):
                    await app.sendGroupMessage(
                        group,
                        MessageChain(f"参数数量不符，需要输入{len(gif_subtitle_memes[key]['pieces'])}段文字，若包含空格请加引号"),
                        quote=message.getFirst(Source)
                    )
                    return
                else:
                    result = await Memes.gif_func(gif_subtitle_memes[key], content)
    if result:
        await app.sendGroupMessage(
            group,
            MessageChain([Image(data_bytes=result.getvalue()) if isinstance(result, BytesIO) else Plain(text=result)]),
            quote=message.getFirst(Source)
        )


class Memes(object):

    @staticmethod
    async def make_luxunsay(texts: List[str]) -> Union[str, BytesIO]:
        font = Memes.load_font(DEFAULT_FONT, 38)
        luxun_font = Memes.load_font(DEFAULT_FONT, 30)
        lines = Memes.wrap_text(texts[0], font, 430)
        if len(lines) > 2:
            return OVER_LENGTH_MSG
        text = '\n'.join(lines)
        spacing = 5
        text_w, text_h = font.getsize_multiline(text, spacing=spacing)
        frame = Memes.load_image('luxunsay.jpg')
        x = 240 - text_w / 2
        y = 350 - text_h / 2
        draw = ImageDraw.Draw(frame)
        draw.multiline_text((x, y), text, font=font,
                            align='center', spacing=spacing, fill=(255, 255, 255))
        draw.text((320, 400), '--鲁迅', font=luxun_font, fill=(255, 255, 255))
        return Memes.save_png(frame)

    @staticmethod
    async def make_nokia(texts: List[str]) -> Union[str, BytesIO]:
        font = Memes.load_font('方正像素14.ttf', 70)
        lines = Memes.wrap_text(texts[0][:900], font, 700)[:5]
        text = '\n'.join(lines)
        angle = -9.3

        img_text = IMG.new('RGBA', (700, 450))
        draw = ImageDraw.Draw(img_text)
        draw.multiline_text((0, 0), text, font=font,
                            spacing=30, fill=(0, 0, 0, 255))
        img_text = img_text.rotate(angle, expand=True)

        head = f'{len(text)}/900'
        img_head = IMG.new('RGBA', font.getsize(head))
        draw = ImageDraw.Draw(img_head)
        draw.text((0, 0), head, font=font, fill=(129, 212, 250, 255))
        img_head = img_head.rotate(angle, expand=True)

        frame = Memes.load_image('nokia.jpg')
        frame.paste(img_text, (205, 330), mask=img_text)
        frame.paste(img_head, (790, 320), mask=img_head)
        return Memes.save_jpg(frame)

    @staticmethod
    async def make_goodnews(texts: List[str]) -> Union[str, BytesIO]:
        text = texts[0]
        fontsize = await Memes.fit_font_size(text, 460, 280, DEFAULT_FONT, 80, 25, 1 / 15)
        if not fontsize:
            return BREAK_LINE_MSG
        font = Memes.load_font(DEFAULT_FONT, fontsize)
        stroke_width = fontsize // 15
        text_w, text_h = font.getsize_multiline(text, stroke_width=stroke_width)

        frame = Memes.load_image('goodnews.jpg')
        draw = ImageDraw.Draw(frame)
        img_w, img_h = frame.size
        x = (img_w - text_w) / 2
        y = (img_h - text_h) / 2
        draw.multiline_text((x, y), text, font=font, fill=(238, 0, 0), align="center",
                            stroke_width=stroke_width, stroke_fill=(255, 255, 153))
        return Memes.save_png(frame)

    @staticmethod
    async def make_jichou(texts: List[str]) -> Union[str, BytesIO]:
        date = datetime.today().strftime('%Y{}%m{}%d{}').format('年', '月', '日')
        text = f"{date} 晴\n{texts[0]}\n这个仇我先记下了"
        font = Memes.load_font(DEFAULT_FONT, 45)
        lines = Memes.wrap_text(text, font, 440)
        if len(lines) > 10:
            return OVER_LENGTH_MSG
        text = '\n'.join(lines)
        spacing = 10
        _, text_h = font.getsize_multiline(text, spacing=spacing)
        frame = Memes.load_image('jichou.png')
        img_w, img_h = frame.size
        bg = IMG.new('RGB', (img_w, img_h + text_h + 20), (255, 255, 255))
        bg.paste(frame, (0, 0))
        draw = ImageDraw.Draw(bg)
        draw.multiline_text((30, img_h + 5), text, font=font,
                            spacing=spacing, fill=(0, 0, 0))
        return Memes.save_jpg(bg)

    @staticmethod
    async def make_fanatic(texts: List[str]) -> Union[str, BytesIO]:
        text = texts[0]
        fontsize = await Memes.fit_font_size(text, 190, 100, DEFAULT_FONT, 70, 30)
        if not fontsize:
            return BREAK_LINE_MSG
        font = Memes.load_font(DEFAULT_FONT, fontsize)
        text_w, text_h = font.getsize_multiline(text)

        frame = Memes.load_image('fanatic.jpg')
        x = 242 - text_w / 2
        y = 90 - text_h / 2
        draw = ImageDraw.Draw(frame)
        draw.multiline_text((x, y), text, align='center',
                            font=font, fill=(0, 0, 0))
        return Memes.save_jpg(frame)

    @staticmethod
    async def make_diyu(texts: List[str]) -> Union[str, BytesIO]:
        text = texts[0]
        fontsize = await Memes.fit_font_size(text, 420, 56, DEFAULT_FONT, 40, 20)
        if not fontsize:
            return OVER_LENGTH_MSG
        font = Memes.load_font(DEFAULT_FONT, fontsize)
        text_w, text_h = font.getsize_multiline(text)

        frame = Memes.load_image('diyu.png')
        draw = ImageDraw.Draw(frame)
        x = 220 - text_w / 2
        y = 272 - text_h / 2
        draw.text((x, y), text, font=font, fill='#000000')
        return Memes.save_png(frame)

    @staticmethod
    async def make_shutup(texts: List[str]) -> Union[str, BytesIO]:
        text = texts[0]
        fontsize = await Memes.fit_font_size(text, 220, 60, DEFAULT_FONT, 40, 20)
        if not fontsize:
            return BREAK_LINE_MSG
        font = Memes.load_font(DEFAULT_FONT, fontsize)
        text_w, text_h = font.getsize_multiline(text)

        frame = Memes.load_image('shutup.jpg')
        draw = ImageDraw.Draw(frame)
        x = 120 - text_w / 2
        y = 195 - text_h / 2
        draw.multiline_text((x, y), text, align='center',
                            font=font, fill=(0, 0, 0))
        return Memes.save_jpg(frame)

    @staticmethod
    async def make_slap(texts: List[str]) -> Union[str, BytesIO]:
        text = texts[0]
        fontsize = await Memes.fit_font_size(text, 600, 180, DEFAULT_FONT, 110, 65)
        if not fontsize:
            return BREAK_LINE_MSG
        font = Memes.load_font(DEFAULT_FONT, fontsize)
        text_w, text_h = font.getsize_multiline(text)

        frame = Memes.load_image('slap.jpg')
        draw = ImageDraw.Draw(frame)
        x = 320 - text_w / 2
        y = 520 - text_h / 2
        draw.multiline_text((x, y), text, align='center',
                            font=font, fill=(0, 0, 0))
        return Memes.save_jpg(frame)

    @staticmethod
    async def make_scroll(texts: List[str]) -> Union[str, BytesIO]:
        text = texts[0]
        text = text.replace('\n', ' ')
        font = Memes.load_font(DEFAULT_FONT, 40)
        text_w, text_h = font.getsize(text)
        if text_w > 600:
            return OVER_LENGTH_MSG

        dialog_left = Memes.load_image('scroll/0.png')
        dialog_right = Memes.load_image('scroll/1.png')
        dialog_box = IMG.new('RGBA', (text_w + 140, 150), '#eaedf4')
        dialog_box.paste(dialog_left, (0, 0))
        dialog_box.paste(IMG.new('RGBA', (text_w, 110), '#ffffff'), (70, 20))
        dialog_box.paste(dialog_right, (text_w + 70, 0))
        draw = ImageDraw.Draw(dialog_box)
        draw.text((70, 95 - text_h), text, font=font, fill='#000000')

        dialog_w, dialog_h = dialog_box.size
        static = IMG.new('RGBA', (dialog_w, dialog_h * 4), '#eaedf4')
        for i in range(4):
            static.paste(dialog_box, (0, dialog_h * i))

        frames = []
        num = 15
        dy = int(dialog_h / num)
        for i in range(num):
            frame = IMG.new('RGBA', static.size)
            frame.paste(static, (0, -dy * i))
            frame.paste(static, (0, static.height - dy * i))
            frames.append(frame)
        return Memes.save_gif(frames, 0.03)

    @staticmethod
    def save_jpg(frame: IMG) -> BytesIO:
        output = BytesIO()
        frame = frame.convert('RGB')
        frame.save(output, format='jpeg')
        return output

    @staticmethod
    def save_png(frame: IMG) -> BytesIO:
        output = BytesIO()
        frame = frame.convert('RGBA')
        frame.save(output, format='png')
        return output

    @staticmethod
    def save_gif(frames, duration: float) -> BytesIO:
        output = BytesIO()
        imageio.mimsave(output, frames, format='gif', duration=duration)
        return output

    @staticmethod
    def load_image(path: str) -> IMG:
        with open(IMAGE_BASE_PATH + path, "rb") as r:
            return IMG.open(BytesIO(r.read()))

    @staticmethod
    def load_font(path: str, fontsize: int) -> FreeTypeFont:
        return ImageFont.truetype(FONT_BASE_PATH + path, fontsize, encoding='utf-8')

    @staticmethod
    def load_thumb(path: str) -> IMG:
        with open(THUMB_BASE_PATH + path, "rb") as r:
            return IMG.open(BytesIO(r.read()))

    @staticmethod
    def wrap_text(text: str, font: FreeTypeFont, max_width: float, stroke_width: int = 0) -> List[str]:
        line = ''
        lines = []
        for t in text:
            if t == '\n':
                lines.append(line)
                line = ''
            elif font.getsize(line + t, stroke_width=stroke_width)[0] > max_width:
                lines.append(line)
                line = t
            else:
                line += t
        lines.append(line)
        return lines

    @staticmethod
    async def fit_font_size(text: str, max_width: float, max_height: float,
                            font_name: str, max_fontsize: int, min_fontsize: int,
                            stroke_ratio: float = 0) -> int:
        fontsize = max_fontsize
        while True:
            font = Memes.load_font(font_name, fontsize)
            width, height = font.getsize_multiline(
                text, stroke_width=int(fontsize * stroke_ratio))
            if width > max_width or height > max_height:
                fontsize -= 1
            else:
                return fontsize
            if fontsize < min_fontsize:
                return 0

    @staticmethod
    async def make_gif(filename: str, texts: List[str], pieces: List[Tuple[int, int]],
                       fontsize: int = 20, padding_x: int = 5, padding_y: int = 5) -> Union[str, BytesIO]:
        img = Memes.load_image(filename)
        frames = []
        for i in range(img.n_frames):
            img.seek(i)
            frames.append(img.convert('RGB'))

        font = Memes.load_font(DEFAULT_FONT, fontsize)
        parts = [frames[start:end] for start, end in pieces]
        img_w, img_h = frames[0].size
        for part, text in zip(parts, texts):
            text_w, text_h = font.getsize(text, stroke_width=1)
            if text_w > img_w - padding_x * 2:
                return OVER_LENGTH_MSG
            x = int((img_w - text_w) / 2)
            y = img_h - text_h - padding_y
            for frame in part:
                draw = ImageDraw.Draw(frame)
                draw.text((x, y), text, font=font, fill=(255, 255, 255),
                          stroke_width=1, stroke_fill=(0, 0, 0))
        return Memes.save_gif(frames, img.info['duration'] / 1000)

    @staticmethod
    async def gif_func(meme_config: dict, texts: List[str]) -> Union[str, BytesIO]:
        return await Memes.make_gif(meme_config['filename'], texts, meme_config['pieces'], meme_config['fontsize'])



gif_subtitle_memes = {
    'wangjingze': {
        'aliases': {'王境泽'},
        'filename': 'wangjingze.gif',
        'thumbnail': 'wangjingze.jpg',
        'pieces': [(0, 9), (12, 24), (25, 35), (37, 48)],
        'fontsize': 20,
        'examples': [
            '我就是饿死',
            '死外边 从这里跳下去',
            '不会吃你们一点东西',
            '真香'
        ]
    },
    'weisuoyuwei': {
        'aliases': {'为所欲为'},
        'filename': 'weisuoyuwei.gif',
        'thumbnail': 'weisuoyuwei.jpg',
        'pieces': [(11, 14), (27, 38), (42, 61), (63, 81), (82, 95),
                   (96, 105), (111, 131), (145, 157), (157, 167)],
        'fontsize': 19,
        'examples': [
            '好啊',
            '就算你是一流工程师',
            '就算你出报告再完美',
            '我叫你改报告你就要改',
            '毕竟我是客户',
            '客户了不起啊',
            'Sorry 客户真的了不起',
            '以后叫他天天改报告',
            '天天改 天天改'
        ]
    },
    'chanshenzi': {
        'aliases': {'馋身子'},
        'filename': 'chanshenzi.gif',
        'thumbnail': 'chanshenzi.jpg',
        'pieces': [(0, 16), (16, 31), (33, 40)],
        'fontsize': 18,
        'examples': [
            '你那叫喜欢吗？',
            '你那是馋她身子',
            '你下贱！'
        ]
    },
    'qiegewala': {
        'aliases': {'切格瓦拉'},
        'filename': 'qiegewala.gif',
        'thumbnail': 'qiegewala.jpg',
        'pieces': [(0, 15), (16, 31), (31, 38), (38, 48), (49, 68), (68, 86)],
        'fontsize': 20,
        'examples': [
            '没有钱啊 肯定要做的啊',
            '不做的话没有钱用',
            '那你不会去打工啊',
            '有手有脚的',
            '打工是不可能打工的',
            '这辈子不可能打工的'
        ]
    },
    'shuifandui': {
        'aliases': {'谁反对'},
        'filename': 'shuifandui.gif',
        'thumbnail': 'shuifandui.jpg',
        'pieces': [(3, 14), (21, 26), (31, 38), (40, 45)],
        'fontsize': 19,
        'examples': [
            '我话说完了',
            '谁赞成',
            '谁反对',
            '我反对'
        ]
    },
    'zengxiaoxian': {
        'aliases': {'曾小贤', '连连看'},
        'filename': 'zengxiaoxian.gif',
        'thumbnail': 'zengxiaoxian.jpg',
        'pieces': [(3, 15), (24, 30), (30, 46), (56, 63)],
        'fontsize': 21,
        'examples': [
            '平时你打电子游戏吗',
            '偶尔',
            '星际还是魔兽',
            '连连看'
        ]
    },
    'yalidaye': {
        'aliases': {'压力大爷'},
        'filename': 'yalidaye.gif',
        'thumbnail': 'yalidaye.jpg',
        'pieces': [(0, 16), (21, 47), (52, 77)],
        'fontsize': 21,
        'examples': [
            '外界都说我们压力大',
            '我觉得吧压力也没有那么大',
            '主要是28岁了还没媳妇儿'
        ]
    },
    'nihaosaoa': {
        'aliases': {'你好骚啊'},
        'filename': 'nihaosaoa.gif',
        'thumbnail': 'nihaosaoa.jpg',
        'pieces': [(0, 14), (16, 26), (42, 61)],
        'fontsize': 17,
        'examples': [
            '既然追求刺激',
            '就贯彻到底了',
            '你好骚啊'
        ]
    },
    'shishilani': {
        'aliases': {'食屎啦你'},
        'filename': 'shishilani.gif',
        'thumbnail': 'shishilani.jpg',
        'pieces': [(14, 21), (23, 36), (38, 46), (60, 66)],
        'fontsize': 17,
        'examples': [
            '穿西装打领带',
            '拿大哥大有什么用',
            '跟着这样的大哥',
            '食屎啦你'
        ]
    },
    'wunian': {
        'aliases': {'五年怎么过的'},
        'filename': 'wunian.gif',
        'thumbnail': 'wunian.jpg',
        'pieces': [(11, 20), (35, 50), (59, 77), (82, 95)],
        'fontsize': 16,
        'examples': [
            '五年',
            '你知道我这五年是怎么过的吗',
            '我每天躲在家里玩贪玩蓝月',
            '你知道有多好玩吗'
        ]
    }
}