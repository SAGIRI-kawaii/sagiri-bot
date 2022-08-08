import os
import PIL.Image
from io import BytesIO
from pathlib import Path
from PIL import ImageDraw
from abc import ABC, abstractmethod
from PIL.ImageFont import FreeTypeFont
from base64 import b64decode, b64encode
from typing import Optional, Union, Tuple, List, Any

from .util import get_font
from .model import TextType

DEFAULT_FONT = str(Path(os.getcwd()) / "statics" / "fonts" / "STKAITI.TTF")


class AbstractElement(ABC):

    center: bool = False  # 是否居中

    @abstractmethod
    def get_canvas_size(self):
        ...


class Text(AbstractElement):

    text: str  # 文本内容

    font: FreeTypeFont = None  # 字体（PIL.ImageFont.FreeTypeFont）

    color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]  # 字体颜色

    size: int  # 字体大小

    spacing: int  # 字间距

    end: str  # 结尾字符

    def __init__(
        self,
        text: str,
        font: Optional[Union[str, Path, FreeTypeFont]] = None,
        color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 0),
        size: int = 40,
        spacing: int = 1,
        text_type: Optional[TextType] = None,
        center: bool = False,
        end: str = "",
    ):
        if text_type:
            self.size = text_type.value["size"]
            self.spacing = text_type.value["spacing"]
        self.text = text
        self.font = get_font(font, size)
        self.color = color
        self.center = center
        self.end = end
        if size:
            self.size = size
        if spacing:
            self.spacing = spacing
        if sum([bool(self.size), bool(self.spacing)]) < 2:
            raise ValueError(
                "Insufficient initialization parameters! "
                "You should give two parameters size and spacing, or one parameter text_type"
            )

    def __add__(self, other: "Text"):
        if all(
            [
                self.font == other.font,
                self.size == other.size,
                self.color == other.color,
                self.spacing == other.spacing,
                self.center == other.center,
            ]
        ):
            self.text = self.get_data() + other.get_data()
            return self
        else:
            raise ValueError("Different attributes cannot be added")

    def __repr__(self):
        return self.text

    def __len__(self):
        return len(self.text + self.end)

    def __iter__(self):
        return iter(self.text + self.end)

    def __getitem__(self, item):
        return self.copy(text=(self.text + self.end)[item])

    def copy(
        self,
        text: Optional[str] = None,
        font: Optional[Union[str, Path, FreeTypeFont]] = None,
        color: Optional[
            Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]
        ] = None,
        size: Optional[int] = None,
        spacing: Optional[int] = None,
        text_type: Optional[TextType] = None,
        center: Optional[bool] = None,
        end: Optional[str] = None,
    ):
        parameters = {
            "text": text or self.text,
            "font": font or self.font,
            "color": color or self.color,
            "size": size or self.size,
            "spacing": spacing or self.spacing,
            "text_type": text_type or None,
            "center": center or self.center,
            "end": end or self.end,
        }

        return Text(**parameters)

    def get_canvas_size(self):
        return (
            self.font.getsize(self.text)[0] + (len(self.text) - 1) * self.spacing,
            self.font.getsize(self.text)[1],
        )

    def get_data(self) -> str:
        return self.text + self.end

    def get_pil_data(self):
        ...

    def split(self, sep: str = "\n") -> List[Union["Text", "Enter"]]:
        texts = (self.text + self.end).split(sep)
        return Enter.join(
            [
                Text(
                    text,
                    self.font,
                    self.color,
                    self.size,
                    self.spacing,
                    None,
                    self.center,
                    self.end,
                )
                if text
                else Null()
                for text in texts
            ]
        )


class Image(AbstractElement):

    base64: Optional[str] = None  # 元素的 base64

    pil_image: PIL.Image.Image  # PIL图片

    self_line: bool  # 图片是否自称一行

    center: bool  # 图片是否居中

    def __init__(
        self,
        *,
        path: Optional[Union[Path, str]] = None,
        base64: Optional[str] = None,
        data_bytes: Optional[bytes] = None,
        self_line: bool = True,
        center: bool = False,
    ):
        if sum([bool(data_bytes), bool(path), bool(base64)]) > 1:
            raise ValueError("Too many binary initializers!")
        if sum([bool(data_bytes), bool(path), bool(base64)]) == 0:
            raise ValueError("Too few binary initializers!")
        self.self_line = self_line if not self.center else True
        self.center = center
        if path:
            if isinstance(path, str):
                path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"{path} is not exist!")
            self.base64 = b64encode(path.read_bytes())
        elif base64:
            self.base64 = base64
        elif data_bytes:
            self.base64 = b64encode(data_bytes)
        self.pil_image = PIL.Image.open(BytesIO(b64decode(self.base64)))

    def get_data(self) -> bytes:
        if self.base64:
            return b64decode(self.base64)
        raise ValueError("base64 value is null")

    def get_pil_data(self) -> PIL.Image.Image:
        return self.pil_image

    def get_canvas_size(self):
        return self.pil_image.size

    def resize(
        self, size: Tuple[int, int], resample=None, box=None, reducing_gap=None
    ) -> PIL.Image.Image:
        self.pil_image = self.pil_image.resize(size, resample, box, reducing_gap)
        return self.pil_image

    @staticmethod
    def draw_ellipse(image, bounds, width=1, antialias=4):
        mask = PIL.Image.new(
            size=[int(dim * antialias) for dim in image.size], mode="L", color="black"
        )
        draw = ImageDraw.Draw(mask)
        for offset, fill in (width / -2.0, "black"), (width / 2.0, "white"):
            left, top = [(value + offset) * antialias for value in bounds[:2]]
            right, bottom = [(value - offset) * antialias for value in bounds[2:]]
            draw.ellipse([left, top, right, bottom], fill=fill)
        mask = mask.resize(image.size, PIL.Image.LANCZOS)
        image.putalpha(mask)

    def round(self) -> PIL.Image:
        self.pil_image.convert("RGBA")
        size = self.pil_image.size
        r2 = min(size[0], size[1])
        if size[0] != size[1]:
            self.pil_image = self.pil_image.resize((r2, r2), PIL.Image.ANTIALIAS)
        ellipse_box = [0, 0, r2 - 2, r2 - 2]
        self.draw_ellipse(self.pil_image, ellipse_box, width=1)
        return self


class Enter(AbstractElement):
    def get_canvas_size(self):
        ...

    @staticmethod
    def join(elements: List[Any]) -> List[Any]:
        result = []
        for element in elements:
            if not isinstance(element, Null):
                result.append(element)
            result.append(Enter())
        return result


class Null(AbstractElement):
    def get_canvas_size(self):
        ...


class EmptyLine(AbstractElement):

    line_height: int  # 空白行高度（空白行只支持自成一行）

    def __init__(self, line_height: int = 40):
        self.line_height = line_height

    def get_canvas_size(self):
        return 1, self.line_height
