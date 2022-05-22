import os
import requests
from abc import ABC
from pathlib import Path
from PIL.ImageFont import FreeTypeFont
from typing import List, Union, Tuple, Optional

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image as GraiaImage
from graia.ariadne.message.element import Plain, At, AtAll, Element

from .elements import Text, Image, TextType
from .util import get_font

DEFAULT_FONT = str(Path(os.getcwd()) / "statics" / "fonts" / "STKAITI.TTF")


class AbstractAdapter(ABC):

    data: List[Union[Text, Image]]


class GraiaAdapter(AbstractAdapter):

    data: List[Union[Text, Image]] = []

    font: Union[str, Path, FreeTypeFont]

    color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]    # 字体颜色

    size: int   # 字体大小

    spacing: int    # 字间距

    center: bool    # 是否居中

    end: str    # 结尾字符

    def __init__(
        self,
        elements: Union[Element, MessageChain, List[Union[Element, MessageChain]]],
        font: Union[str, Path, FreeTypeFont] = DEFAULT_FONT,
        color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 0),
        size: int = 40,
        spacing: int = 1,
        text_type: Optional[TextType] = None,
        center: bool = False,
        end: str = ''
    ):
        self.data = []
        if not isinstance(elements, list):
            elements = [elements]
        if text_type:
            self.size = text_type.value["size"]
            self.spacing = text_type.value["spacing"]
        self.font = get_font(font, size)
        self.color = color
        self.center = center
        self.end = end
        if size:
            self.size = size
        if spacing:
            self.spacing = spacing
        self.parse(elements)

    def parse(self, elements: List[Union[MessageChain, Element]]):
        for element in elements:
            if isinstance(element, MessageChain):
                messagechain_elements = element.asSendable().__root__
                self.parse(messagechain_elements)
            elif any(isinstance(element, el_type) for el_type in (Plain, At, AtAll)):
                self.data.append(
                    Text(
                        element.asDisplay(), self.font, self.color, self.size, self.spacing, None, self.center, self.end
                    )
                )
            elif isinstance(element, GraiaImage):
                if element.base64:
                    self.data.append(Image(base64=element.base64, center=self.center))
                elif element.url:
                    self.data.append(Image(data_bytes=requests.get(element.url, verify=False).content, center=self.center))
                else:
                    raise ValueError("Can't init Image without url or base64!")
            else:
                raise ValueError(f"Unsupported element type: {type(element)}")
