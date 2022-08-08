import os
from pathlib import Path
from PIL import ImageFont
from typing import Union, Optional
from PIL.ImageFont import FreeTypeFont

DEFAULT_FONT_NAME = str(Path(os.getcwd()) / "statics" / "fonts" / "STKAITI.TTF")
DEFAULT_FONT = ImageFont.truetype(DEFAULT_FONT_NAME, 40)

fonts = {DEFAULT_FONT_NAME: {40: DEFAULT_FONT}}


def get_font(
    font: Optional[Union[str, Path, FreeTypeFont]] = None, size: int = 40
) -> FreeTypeFont:
    if not font:
        if size in fonts[DEFAULT_FONT_NAME]:
            return DEFAULT_FONT
        else:
            fonts[DEFAULT_FONT_NAME][size] = ImageFont.truetype(DEFAULT_FONT_NAME, size)
            return fonts[DEFAULT_FONT_NAME][size]
    if isinstance(font, FreeTypeFont):
        return font
    elif str(font) in fonts:
        if size in fonts[str(font)]:
            return fonts[str(font)][size]
        else:
            fonts[str(font)][size] = ImageFont.truetype(str(font), size)
            return fonts[str(font)][size]
    else:
        fonts[str(font)] = {}
        fonts[str(font)][size] = ImageFont.truetype(str(font), size)
        return fonts[str(font)][size]
