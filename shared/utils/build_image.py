import asyncio
from typing import Tuple, Literal, List
from pathlib import Path
from io import BytesIO
from PIL import ImageFont, ImageDraw, ImageFilter
import PIL.Image
import base64


class BuildImage:
    """
    快捷生成图片与操作图片的工具类
    """

    def __init__(
        self,
        w: int,
        h: int,
        paste_image_width: int = 0,
        paste_image_height: int = 0,
        color: str | Tuple[int, int, int] | Tuple[int, int, int, int] | None = None,
        image_mode: Literal["1", "CMYK", "F", "HSV", "I", "L", "LAB", "P", "RGB", "RGBA", "RGBX", "YCbCr"] = "RGBA",
        font_size: int = 10,
        background: str | BytesIO | Path | None = None,
        font: str | Path = Path.cwd() / "resources" / "fonts" / "yz.ttf",
        ratio: float = 1,
        is_alpha: bool = False,
        plain_text: str | None = None,
        font_color: str | Tuple[int, int, int] | None = None,
    ):
        """
        参数：
            :param w: 自定义图片的宽度，w=0时为图片原本宽度
            :param h: 自定义图片的高度，h=0时为图片原本高度
            :param paste_image_width: 当图片做为背景图时，设置贴图的宽度，用于贴图自动换行
            :param paste_image_height: 当图片做为背景图时，设置贴图的高度，用于贴图自动换行
            :param color: 生成图片的颜色
            :param image_mode: 图片的类型
            :param font_size: 文字大小
            :param background: 打开图片的路径
            :param font: 字体，默认在 resource/ttf/ 路径下
            :param ratio: 倍率压缩
            :param is_alpha: 是否背景透明
            :param plain_text: 纯文字文本
        """
        self.w = int(w)
        self.h = int(h)
        self.paste_image_width = int(paste_image_width)
        self.paste_image_height = int(paste_image_height)
        self.current_w = 0
        self.current_h = 0
        self.font = ImageFont.truetype(font, int(font_size))
        if not plain_text and not color:
            color = (255, 255, 255)
        self.background = background
        if not background:
            if plain_text:
                if not color:
                    color = (255, 255, 255, 0)
                ttf_w, ttf_h = self.getsize(plain_text)
                self.w = self.w if self.w > ttf_w else ttf_w
                self.h = self.h if self.h > ttf_h else ttf_h
            self.markImg = PIL.Image.new(image_mode, (self.w, self.h), color)
            self.markImg.convert(image_mode)
        else:
            if not w and not h:
                self.markImg = PIL.Image.open(background)
                w, h = self.markImg.size
                if ratio and ratio > 0 and ratio != 1:
                    self.w = int(ratio * w)
                    self.h = int(ratio * h)
                    self.markImg = self.markImg.resize((self.w, self.h), PIL.Image.ANTIALIAS)
                else:
                    self.w = w
                    self.h = h
            else:
                self.markImg = PIL.Image.open(background).resize(
                    (self.w, self.h), PIL.Image.ANTIALIAS
                )
        if is_alpha:
            array = self.markImg.load()
            for i in range(w):
                for j in range(h):
                    pos = array[i, j]
                    is_edit = sum([1 for x in pos[0:3] if x > 240]) == 3
                    if is_edit:
                        array[i, j] = (255, 255, 255, 0)
        self.draw = ImageDraw.Draw(self.markImg)
        self.size = self.w, self.h
        if plain_text:
            fill = font_color if font_color else (0, 0, 0)
            self.text((0, 0), plain_text, fill)
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self.loop = asyncio.get_event_loop()

    async def apaste(
        self,
        img: "BuildImage" or PIL.Image,
        pos: Tuple[int, int] = None,
        alpha: bool = False,
        center_type: Literal["center", "by_height", "by_width"] | None = None,
    ):
        """
        说明：
            异步 贴图
        参数：
            :param img: 已打开的图片文件，可以为 BuildImage 或 Image
            :param pos: 贴图位置（左上角）
            :param alpha: 图片背景是否为透明
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        await self.loop.run_in_executor(None, self.paste, img, pos, alpha, center_type)

    def paste(
        self,
        img: "BuildImage" or PIL.Image,
        pos: Tuple[int, int] = None,
        alpha: bool = False,
        center_type: Literal["center", "by_height", "by_width"] | None = None,
    ):
        """
        说明：
            贴图
        参数：
            :param img: 已打开的图片文件，可以为 BuildImage 或 Image
            :param pos: 贴图位置（左上角）
            :param alpha: 图片背景是否为透明
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        if center_type:
            if center_type not in ["center", "by_height", "by_width"]:
                raise ValueError(
                    "center_type must be 'center', 'by_width' or 'by_height'"
                )
            width, height = 0, 0
            if not pos:
                pos = (0, 0)
            if center_type == "center":
                width = int((self.w - img.w) / 2)
                height = int((self.h - img.h) / 2)
            elif center_type == "by_width":
                width = int((self.w - img.w) / 2)
                height = pos[1]
            elif center_type == "by_height":
                width = pos[0]
                height = int((self.h - img.h) / 2)
            pos = (width, height)
        if isinstance(img, BuildImage):
            img = img.markImg
        if self.current_w == self.w:
            self.current_w = 0
            self.current_h += self.paste_image_height
        if not pos:
            pos = (self.current_w, self.current_h)
        if alpha:
            try:
                self.markImg.paste(img, pos, img)
            except ValueError:
                img = img.convert("RGBA")
                self.markImg.paste(img, pos, img)
        else:
            self.markImg.paste(img, pos)
        self.current_w += self.paste_image_width

    def getsize(self, msg: str) -> Tuple[int, int]:
        """
        说明：
            获取文字在该图片 font_size 下所需要的空间
        参数：
            :param msg: 文字内容
        """
        return self.font.getsize(msg)

    async def apoint(
        self, pos: Tuple[int, int], fill: Tuple[int, int, int] | None = None
    ):
        """
        说明：
            异步 绘制多个或单独的像素
        参数：
            :param pos: 坐标
            :param fill: 填错颜色
        """
        await self.loop.run_in_executor(None, self.point, pos, fill)

    def point(self, pos: Tuple[int, int], fill: Tuple[int, int, int] | None = None):
        """
        说明：
            绘制多个或单独的像素
        参数：
            :param pos: 坐标
            :param fill: 填错颜色
        """
        self.draw.point(pos, fill=fill)

    async def aellipse(
        self,
        pos: Tuple[int, int, int, int],
        fill: Tuple[int, int, int] | None = None,
        outline: Tuple[int, int, int] | None = None,
        width: int = 1,
    ):
        """
        说明：
            异步 绘制圆
        参数：
            :param pos: 坐标范围
            :param fill: 填充颜色
            :param outline: 描线颜色
            :param width: 描线宽度
        """
        await self.loop.run_in_executor(None, self.ellipse, pos, fill, outline, width)

    def ellipse(
        self,
        pos: Tuple[int, int, int, int],
        fill: Tuple[int, int, int] | None = None,
        outline: Tuple[int, int, int] | None = None,
        width: int = 1,
    ):
        """
        说明：
            绘制圆
        参数：
            :param pos: 坐标范围
            :param fill: 填充颜色
            :param outline: 描线颜色
            :param width: 描线宽度
        """
        self.draw.ellipse(pos, fill, outline, width)

    async def atext(
        self,
        pos: Tuple[int, int],
        text: str,
        fill: str | Tuple[int, int, int] = (0, 0, 0),
        center_type: Literal["center", "by_height", "by_width"] | None = None,
    ):
        """
        说明：
            异步 在图片上添加文字
        参数：
            :param pos: 文字位置
            :param text: 文字内容
            :param fill: 文字颜色
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        await self.loop.run_in_executor(None, self.text, pos, text, fill, center_type)

    def text(
        self,
        pos: Tuple[int, int],
        text: str,
        fill: str | Tuple[int, int, int] = (0, 0, 0),
        center_type: Literal["center", "by_height", "by_width"] | None = None,
    ):
        """
        说明：
            在图片上添加文字
        参数：
            :param pos: 文字位置
            :param text: 文字内容
            :param fill: 文字颜色
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        if center_type:
            if center_type not in ["center", "by_height", "by_width"]:
                raise ValueError(
                    "center_type must be 'center', 'by_width' or 'by_height'"
                )
            w, h = self.w, self.h
            ttf_w, ttf_h = self.getsize(text)
            if center_type == "center":
                w = int((w - ttf_w) / 2)
                h = int((h - ttf_h) / 2)
            elif center_type == "by_width":
                w = int((w - ttf_w) / 2)
                h = pos[1]
            elif center_type == "by_height":
                h = int((h - ttf_h) / 2)
                w = pos[0]
            pos = (w, h)
        self.draw.text(pos, text, fill=fill, font=self.font)

    async def asave(self, path: str | Path | None = None):
        """
        说明：
            异步 保存图片
        参数：
            :param path: 图片路径
        """
        await self.loop.run_in_executor(None, self.save, path)

    def save(self, path: str | Path | None = None):
        """
        说明：
            保存图片
        参数：
            :param path: 图片路径
        """
        if not path:
            path = self.background
        self.markImg.save(path)

    def show(self):
        """
        说明：
            显示图片
        """
        self.markImg.show(self.markImg)

    async def aresize(self, ratio: float = 0, w: int = 0, h: int = 0):
        """
        说明：
            异步 压缩图片
        参数：
            :param ratio: 压缩倍率
            :param w: 压缩图片宽度至 w
            :param h: 压缩图片高度至 h
        """
        await self.loop.run_in_executor(None, self.resize, ratio, w, h)

    def resize(self, ratio: float = 0, w: int = 0, h: int = 0):
        """
        说明：
            压缩图片
        参数：
            :param ratio: 压缩倍率
            :param w: 压缩图片宽度至 w
            :param h: 压缩图片高度至 h
        """
        if not w and not h:
            if not ratio:
                raise ValueError("缺少参数...")
            w = int(self.w * ratio)
            h = int(self.h * ratio)
        self.markImg = self.markImg.resize((w, h), PIL.Image.ANTIALIAS)
        self.w, self.h = self.markImg.size
        self.size = self.w, self.h
        self.draw = ImageDraw.Draw(self.markImg)

    async def acrop(self, box: Tuple[int, int, int, int]):
        """
        说明：
            异步 裁剪图片
        参数：
            :param box: 左上角坐标，右下角坐标 (left, upper, right, lower)
        """
        await self.loop.run_in_executor(None, self.crop, box)

    def crop(self, box: Tuple[int, int, int, int]):
        """
        说明：
            裁剪图片
        参数：
            :param box: 左上角坐标，右下角坐标 (left, upper, right, lower)
        """
        self.markImg = self.markImg.crop(box)
        self.w, self.h = self.markImg.size
        self.size = self.w, self.h
        self.draw = ImageDraw.Draw(self.markImg)

    def check_font_size(self, word: str) -> bool:
        """
        说明：
            检查文本所需宽度是否大于图片宽度
        参数：
            :param word: 文本内容
        """
        return self.font.getsize(word)[0] > self.w

    async def atransparent(self, alpha_ratio: float = 1, n: int = 0):
        """
        说明：
            异步 图片透明化
        参数：
            :param alpha_ratio: 透明化程度
            :param n: 透明化大小内边距
        """
        await self.loop.run_in_executor(None, self.transparent, alpha_ratio, n)

    def transparent(self, alpha_ratio: float = 1, n: int = 0):
        """
        说明：
            图片透明化
        参数：
            :param alpha_ratio: 透明化程度
            :param n: 透明化大小内边距
        """
        self.markImg = self.markImg.convert("RGBA")
        x, y = self.markImg.size
        for i in range(n, x - n):
            for k in range(n, y - n):
                color = self.markImg.getpixel((i, k))
                color = color[:-1] + (int(100 * alpha_ratio),)
                self.markImg.putpixel((i, k), color)
        self.draw = ImageDraw.Draw(self.markImg)

    def pic2bs4(self) -> str:
        """
        说明：
            BuildImage 转 base64
        """
        buf = BytesIO()
        self.markImg.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def pic2bytes(self) -> bytes:
        """
        说明：
            BuildImage 转 base64
        """
        buf = BytesIO()
        self.markImg.save(buf, format="PNG")
        return buf.getvalue()

    def convert(self, type_: str):
        """
        说明：
            修改图片类型
        参数：
            :param type_: 类型
        """
        self.markImg = self.markImg.convert(type_)

    async def arectangle(
        self,
        xy: Tuple[int, int, int, int],
        fill: Tuple[int, int, int] | None = None,
        outline: str = None,
        width: int = 1,
    ):
        """
        说明：
            异步 画框
        参数：
            :param xy: 坐标
            :param fill: 填充颜色
            :param outline: 轮廓颜色
            :param width: 线宽
        """
        await self.loop.run_in_executor(None, self.rectangle, xy, fill, outline, width)

    def rectangle(
        self,
        xy: Tuple[int, int, int, int],
        fill: Tuple[int, int, int] | None = None,
        outline: str = None,
        width: int = 1,
    ):
        """
        说明：
            画框
        参数：
            :param xy: 坐标
            :param fill: 填充颜色
            :param outline: 轮廓颜色
            :param width: 线宽
        """
        self.draw.rectangle(xy, fill, outline, width)

    async def apolygon(
        self,
        xy: List[Tuple[int, int]],
        fill: Tuple[int, int, int] = (0, 0, 0),
        outline: int = 1,
    ):
        """
        说明:
            异步 画多边形
        参数：
            :param xy: 坐标
            :param fill: 颜色
            :param outline: 线宽
        """
        await self.loop.run_in_executor(None, self.polygon, xy, fill, outline)

    def polygon(
        self,
        xy: List[Tuple[int, int]],
        fill: Tuple[int, int, int] = (0, 0, 0),
        outline: int = 1,
    ):
        """
        说明:
            画多边形
        参数：
            :param xy: 坐标
            :param fill: 颜色
            :param outline: 线宽
        """
        self.draw.polygon(xy, fill, outline)

    async def aline(
        self,
        xy: Tuple[int, int, int, int],
        fill: str | Tuple[int, int, int] | None = None,
        width: int = 1,
    ):
        """
        说明：
            异步 画线
        参数：
            :param xy: 坐标
            :param fill: 填充
            :param width: 线宽
        """
        await self.loop.run_in_executor(None, self.line, xy, fill, width)

    def line(
        self,
        xy: Tuple[int, int, int, int],
        fill: Tuple[int, int, int] | str | None = None,
        width: int = 1,
    ):
        """
        说明：
            画线
        参数：
            :param xy: 坐标
            :param fill: 填充
            :param width: 线宽
        """
        self.draw.line(xy, fill, width)

    async def acircle(self):
        """
        说明：
            异步 将 BuildImage 图片变为圆形
        """
        await self.loop.run_in_executor(None, self.circle)

    def circle(self):
        """
        说明：
            将 BuildImage 图片变为圆形
        """
        self.convert("RGBA")
        r2 = min(self.w, self.h)
        if self.w != self.h:
            self.resize(w=r2, h=r2)
        r3 = int(r2 / 2)
        imb = PIL.Image.new("RGBA", (r3 * 2, r3 * 2), (255, 255, 255, 0))
        pim_a = self.markImg.load()  # 像素的访问对象
        pim_b = imb.load()
        r = float(r2 / 2)
        for i in range(r2):
            lx = abs(i - r)  # 到圆心距离的横坐标
            for j in range(r2):
                ly = abs(j - r)  # 到圆心距离的纵坐标
                l_ = (pow(lx, 2) + pow(ly, 2)) ** 0.5  # 三角函数 半径
                if l_ < r3:
                    pim_b[i - (r - r3), j - (r - r3)] = pim_a[i, j]
        self.markImg = imb

    async def acircle_corner(self, radii: int = 30):
        """
        说明：
            异步 矩形四角变圆
        参数：
            :param radii: 半径
        """
        await self.loop.run_in_executor(None, self.circle_corner, radii)

    def circle_corner(self, radii: int = 30):
        """
        说明：
            矩形四角变圆
        参数：
            :param radii: 半径
        """
        # 画圆（用于分离4个角）
        circle = PIL.Image.new("L", (radii * 2, radii * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)
        self.markImg = self.markImg.convert("RGBA")
        w, h = self.markImg.size
        alpha = PIL.Image.new("L", self.markImg.size, 255)
        alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))
        alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))
        alpha.paste(
            circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii)
        )
        alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))
        self.markImg.putalpha(alpha)

    async def arotate(self, angle: int, expand: bool = False):
        """
        说明：
            异步 旋转图片
        参数：
            :param angle: 角度
            :param expand: 放大图片适应角度
        """
        await self.loop.run_in_executor(None, self.rotate, angle, expand)

    def rotate(self, angle: int, expand: bool = False):
        """
        说明：
            旋转图片
        参数：
            :param angle: 角度
            :param expand: 放大图片适应角度
        """
        self.markImg = self.markImg.rotate(angle, expand=expand)

    async def atranspose(self, angle: int):
        """
        说明：
            异步 旋转图片(包括边框)
        参数：
            :param angle: 角度
        """
        await self.loop.run_in_executor(None, self.transpose, angle)

    def transpose(self, angle: Literal[0, 1, 2, 3, 4, 5, 6]):
        """
        说明：
            旋转图片(包括边框)
        参数：
            :param angle: 角度
        """
        self.markImg.transpose(angle)

    async def afilter(self, filter_: str, aud: int = None):
        """
        说明：
            异步 图片变化
        参数：
            :param filter_: 变化效果
            :param aud: 利率
        """
        await self.loop.run_in_executor(None, self.filter, filter_, aud)

    def filter(self, filter_: str, aud: int = None):
        """
        说明：
            图片变化
        参数：
            :param filter_: 变化效果
            :param aud: 利率
        """
        _x = None
        if filter_ == "BLUR":
            _x = ImageFilter.BLUR
        elif filter_ == "CONTOUR":
            _x = ImageFilter.CONTOUR
        elif filter_ == "EDGE_ENHANCE":
            _x = ImageFilter.EDGE_ENHANCE
        elif filter_ == "FIND_EDGES":
            _x = ImageFilter.FIND_EDGES
        elif filter_ == "GaussianBlur":
            _x = ImageFilter.GaussianBlur
        if _x:
            self.markImg = self.markImg.filter(_x(aud)) if aud else self.markImg.filter(_x)
        self.draw = ImageDraw.Draw(self.markImg)

    async def areplace_color_tran(
        self,
        src_color: Tuple[int, int, int] | Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        replace_color: Tuple[int, int, int],
    ):
        """
        说明：
            异步 颜色替换
        参数：
            :param src_color: 目标颜色，或者使用列表，设置阈值
            :param replace_color: 替换颜色
        """
        self.loop.run_in_executor(
            None, self.replace_color_tran, src_color, replace_color
        )

    def replace_color_tran(
        self,
        src_color: Tuple[int, int, int] | Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        replace_color: Tuple[int, int, int]
    ):
        """
        说明：
            颜色替换
        参数：
            :param src_color: 目标颜色，或者使用元祖，设置阈值
            :param replace_color: 替换颜色
        """
        if isinstance(src_color, tuple):
            start_ = src_color[0]
            end_ = src_color[1]
        else:
            start_ = src_color
            end_ = None
        for i in range(self.w):
            for j in range(self.h):
                r, g, b = self.markImg.getpixel((i, j))
                if end_:
                    if start_[0] <= r <= end_[0] and start_[1] <= g <= end_[1] and start_[2] <= b <= end_[2]:
                        self.markImg.putpixel((i, j), replace_color)
                elif r == start_[0] and g == start_[1] and b == start_[2]:
                    self.markImg.putpixel((i, j), replace_color)

    #
    def getchannel(self, type_):
        self.markImg = self.markImg.getchannel(type_)

    @staticmethod
    def draw_ellipse(image, bounds, width=1, outline="white", antialias=4):
        """Improved ellipse drawing function, based on PIL.ImageDraw."""

        # Use a single channel image (mode='L') as mask.
        # The size of the mask can be increased relative to the imput image
        # to get smoother looking results.
        mask = PIL.Image.new(
            size=(int(image.size[0] * antialias),
                  int(image.size[1] * antialias)),
            mode="L", color="black"
        )

        draw = ImageDraw.Draw(mask)

        # draw outer shape in white (color) and inner shape in black (transparent)
        for offset, fill in (width / -2.0, "black"), (width / 2.0, "white"):
            left, top = [(value + offset) * antialias for value in bounds[:2]]
            right, bottom = [(value - offset) * antialias for value in bounds[2:]]
            draw.ellipse([left, top, right, bottom], fill=fill)

        # downsample the mask using PIL.Image.LANCZOS
        # (a high-quality downsampling filter).
        mask = mask.resize(image.size, PIL.Image.LANCZOS)

        # paste outline color to input image through the mask
        image.putalpha(mask)

    #
    def circle_new(self):
        self.markImg.convert("RGBA")
        size = self.markImg.size
        r2 = min(size[0], size[1])
        if size[0] != size[1]:
            self.markImg = self.markImg.resize((r2, r2), PIL.Image.ANTIALIAS)
        ellipse_box = [0, 0, r2 - 2, r2 - 2]
        self.draw_ellipse(self.markImg, ellipse_box, width=1)
