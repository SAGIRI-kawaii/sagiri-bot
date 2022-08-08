import math
import PIL.Image
from io import BytesIO
from pathlib import Path
from PIL import ImageDraw
from PIL.ImageFont import FreeTypeFont
from typing import List, Union, Optional, Tuple, Literal

from .adapter import AbstractAdapter
from .elements import Text, Image, Enter, EmptyLine


class TextEngine(object):
    """一个文字转图片的引擎"""

    elements: List[Union[Text, Image]]  # 内容元素

    max_width: int  # 最大宽度（image_adaption=False时起作用）

    min_width: int  # 最小宽度（image_adaption=False时起作用）

    size: Optional[Tuple[int, int]] = None  # 画布尺寸

    drawing_size: Optional[Tuple[int, int]] = None  # 可绘图尺寸（除去页边距）

    padding_x: int  # 水平方向页边距

    padding_y: int  # 垂直方向页边距

    line_spacing: int  # 行间距

    image_adaption: bool  # 图片自适应大小

    image_mode: Literal["1", "L", "P", "RGB", "RGBA", "CMYK", "YCbCr", "I", "F"]  # 图片格式

    canvas: ImageDraw  # 画布

    canvas_image: PIL.Image.Image  # 画布图片

    bg_color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]  # 背景颜色

    sep: str  # 元素间间隔符

    def __init__(
        self,
        elements: List[
            Union[AbstractAdapter, str, bytes, BytesIO, PIL.Image.Image, Text, Image]
        ],
        max_width: int = 4096,
        min_width: int = 1080,
        font_size: int = 40,
        spacing: int = 15,
        padding_x: int = 20,
        padding_y: int = 15,
        line_spacing: int = 15,
        image_adaption: bool = True,
        image_mode: Literal[
            "1", "L", "P", "RGB", "RGBA", "CMYK", "YCbCr", "I", "F"
        ] = "RGBA",
        font: Optional[Union[str, Path, FreeTypeFont]] = "STKAITI.TTF",
        bg_color: Optional[
            Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]
        ] = (255, 255, 255, 255),
        sep: str = "\n",
    ):
        self.elements = []
        self.max_width = max_width
        self.min_width = min_width
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.line_spacing = line_spacing
        self.image_adaption = image_adaption
        self.image_mode = image_mode
        self.bg_color = bg_color
        self.sep = sep

        for element in elements:
            if isinstance(element, AbstractAdapter):
                self.elements.extend(element.data)
            elif isinstance(element, str):
                self.elements.append(
                    Text(element, font, size=font_size, spacing=spacing)
                )
            elif isinstance(element, bytes):
                self.elements.append(Image(data_bytes=element))
            elif isinstance(element, BytesIO):
                self.elements.append(Image(data_bytes=element.getvalue()))
            elif isinstance(element, PIL.Image.Image):
                self.elements.append(Image(data_bytes=element.getvalue()))
            else:
                self.elements.append(element)
        self.merge_and_split()

    def draw(self, show: bool = False) -> bytes:
        if not self.size:
            self.size = self.get_canvas_size()
        if self.bg_color:
            self.canvas_image = PIL.Image.new(
                self.image_mode, self.size, color=self.bg_color
            )
        else:
            self.canvas_image = PIL.Image.new(
                self.image_mode,
                self.size,
            )
        self.canvas = ImageDraw.Draw(self.canvas_image)
        current_x, current_y = self.padding_x, self.padding_y
        current_font_height = 0
        for element in self.elements:
            if isinstance(element, Text):
                center_changed = False
                if current_font_height:
                    current_y += current_font_height
                    current_font_height = 0
                for i in range(len(element.text)):
                    char = element.text[i]
                    if all(
                        [
                            element.center,
                            current_x
                            + element[i:].get_canvas_size()[0]
                            + element.spacing
                            <= self.drawing_size[0],
                            not center_changed,
                        ]
                    ):
                        current_x = self.padding_x + int(
                            (self.drawing_size[0] - element[i:].get_canvas_size()[0])
                            / 2
                        )
                        center_changed = True
                    if char == "\n":
                        current_y += element.get_canvas_size()[1] + self.line_spacing
                        current_x = self.padding_x
                        continue
                    if char == "\r":
                        continue
                    if (
                        current_x + element.font.getsize(char)[0]
                        > self.drawing_size[0] + self.padding_x
                    ):
                        current_y += element.get_canvas_size()[1] + self.line_spacing
                        current_x = self.padding_x
                        if all(
                            [
                                element.center,
                                current_x
                                + element[i:].get_canvas_size()[0]
                                + element.spacing
                                <= self.drawing_size[0],
                                not center_changed,
                            ]
                        ):
                            current_x = self.padding_x + int(
                                (
                                    self.drawing_size[0]
                                    - element[i:].get_canvas_size()[0]
                                )
                                / 2
                            )
                            center_changed = True
                    self.canvas.text(
                        (current_x, current_y),
                        char,
                        font=element.font,
                        fill=element.color,
                    )
                    current_x += element.font.getsize(char)[0] + element.spacing
                current_font_height = element.get_canvas_size()[1]
            elif isinstance(element, Image):
                image_width, image_height = element.get_canvas_size()
                if (
                    element.self_line
                    or image_width + current_x > self.drawing_size[0] + self.padding_x
                ):
                    if current_font_height:
                        current_y += current_font_height
                        current_font_height = 0
                    current_x = self.padding_x
                    current_y += self.line_spacing
                image_height = (
                    int(image_height * self.drawing_size[0] / image_width)
                    if self.image_adaption
                    else image_height
                )
                image = (
                    element.resize((self.drawing_size[0], image_height))
                    if self.image_adaption
                    else element.pil_image
                )
                self.canvas_image.paste(image, (current_x, current_y))
                current_font_height = (
                    image_height if not element.self_line else current_font_height
                )
                current_x += image_width if not element.self_line else 0
                current_y += (
                    image_height + self.line_spacing if element.self_line else 0
                )
            elif isinstance(element, Enter):
                # if current_font_height:
                #     current_y += current_font_height
                current_x = self.padding_x
                current_y += self.line_spacing
            elif isinstance(element, EmptyLine):
                current_x = self.padding_x
                current_y += element.line_height + self.line_spacing * 2
                current_font_height = 0
            else:
                raise ValueError(f"Unsupported element type: {type(element)}")
        if show:
            self.canvas_image.show()
        bytes_io = BytesIO()
        self.canvas_image.save(bytes_io, format="PNG")
        return bytes_io.getvalue()

    def get_canvas_size(self) -> Tuple[int, int]:
        if self.size:
            return self.size
        else:
            text_sizes = [
                element.get_canvas_size()
                for element in self.elements
                if isinstance(element, Text)
            ]
            image_sizes = [
                element.get_canvas_size()
                for element in self.elements
                if isinstance(element, Image)
            ]
            height = 0
            current_width, current_height = 0, 0
            if not self.image_adaption:
                if image_sizes:
                    width = max([self.max_width, *[size[0] for size in image_sizes]])
                else:
                    text_max_width = max([size[0] for size in text_sizes])
                    width = (
                        self.max_width
                        if text_max_width >= self.max_width
                        else (
                            self.min_width
                            if text_max_width <= self.min_width
                            else text_max_width
                        )
                    )
            else:
                width = min(
                    [
                        self.min_width,
                        *[size[0] for size in image_sizes],
                        *[size[0] for size in text_sizes],
                    ]
                )
                if width < self.min_width:
                    width = self.min_width
            # print(width)
            for element in self.elements:
                size = element.get_canvas_size()
                # print(element.__class__.__name__, size, width, '*', height, str(element).strip())
                if isinstance(element, Text):
                    height += current_height if current_height else 0
                    current_height = 0
                    if size[0] + current_width > width:
                        height += current_height + self.line_spacing
                        height += math.ceil(
                            ((size[0] + current_width) / width + 1)
                            * (size[1] + self.line_spacing)
                        )
                        current_height = (
                            size[1] if size[1] > current_height else current_height
                        )
                        current_width = (current_width + size[0]) % width
                    else:
                        current_width += size[0] + element.spacing
                        current_height = (
                            size[1] if size[1] > current_height else current_height
                        )
                elif isinstance(element, Image):
                    if (
                        element.self_line
                        or current_width + size[0] > width
                        or element.center
                    ):
                        # print(current_width, current_height, current_width + size[0])
                        height += current_height + self.line_spacing
                        current_width, current_height = 0, 0
                        height += (
                            int(size[1] * width / size[0])
                            if self.image_adaption
                            else size[1] + self.line_spacing
                        )
                    else:
                        current_height = (
                            size[1] if size[1] > current_height else current_height
                        )
                        current_width += size[0]
                elif isinstance(element, Enter):
                    height += current_height + self.line_spacing
                    current_width, current_height = 0, 0
                elif isinstance(element, EmptyLine):
                    height += (
                        current_height + self.line_spacing * 2 + element.line_height
                    )
                    current_width, current_height = 0, 0
            height += current_height
            self.drawing_size = (int(width), int(height))
            self.size = (
                int(width) + self.padding_x * 2,
                int(height) + self.padding_y * 2,
            )
            return self.size

    def merge_and_split(self, sep: str = "\n") -> "TextEngine":
        elements = []
        temp_element = []
        for element in self.elements:
            if isinstance(element, Text):
                temp_element.append(element)
            elif any(
                [
                    isinstance(element, element_type)
                    for element_type in (Image, Enter, EmptyLine)
                ]
            ):
                if temp_element:
                    elements.extend(self.text_merge(temp_element))
                    temp_element = []
                elements.append(element)
        elements.extend(self.text_merge(temp_element))
        temp_element = elements[:]
        elements = []
        for element in temp_element:
            if isinstance(element, Text):
                elements.extend(element.split(sep))
            elif any(
                isinstance(element, element_type)
                for element_type in (Image, Enter, EmptyLine)
            ):
                elements.append(element)
        self.elements = elements

        return self

    @staticmethod
    def text_merge(text_list: List[Text]) -> List[Text]:
        if len(text_list) <= 1:
            return text_list
        result = []
        while len(text_list) > 1:
            if all(
                [
                    text_list[0].font == text_list[1].font,
                    text_list[0].size == text_list[1].size,
                    text_list[0].color == text_list[1].color,
                    text_list[0].spacing == text_list[1].spacing,
                    text_list[0].center == text_list[1].center,
                ]
            ):
                new_text = text_list[0] + text_list[1]
                text_list.pop(0)
                text_list[0] = new_text
            else:
                result.append(text_list[0])
                text_list.pop(0)
        result.append(text_list[0])
        return result
