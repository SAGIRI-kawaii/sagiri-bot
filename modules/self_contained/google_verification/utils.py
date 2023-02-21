from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from typing import Literal
from pathlib import Path

FONT_BIG = ImageFont.truetype(str(Path.cwd() / "resources" / "fonts" / "ArialEnUnicodeBold.ttf"), 40)
FONT_SMALL = ImageFont.truetype(str(Path.cwd() / "resources" / "fonts" / "ArialEnUnicodeBold.ttf"), 20)
ZH_TOP = "请选择包含"
ZH_BOTTOM = "的所有图块，如果没有，请点击“跳过”"
EN_TOP = "Select all squares with"
EN_BOTTOM = "If there are none, clik skip"


def gen_verification(name: str, image: bytes, language: Literal["en", "zh"] = "zh") -> bytes:
    image = Image.open(BytesIO(image))
    image = image.resize((900, 900))
    canvas = Image.new("RGB", (1000, 1535), "#FFF")
    length = 233
    for i in range(4):
        for j in range(4):
            box = (length * i, length * j, length * (i + 1), length * (j + 1))
            canvas.paste(image.crop(box), (19 + i * (233 + 10), 370 + j * (233 + 10)))

    banner = Image.new("RGB", (962, 332), "#4790E4")
    draw = ImageDraw.Draw(banner)
    draw.text((70, 100), ZH_TOP if language == "zh" else EN_TOP, "white", FONT_SMALL)
    draw.text((70, 160), name, "white", FONT_BIG)
    draw.text((70, 230), ZH_BOTTOM if language == "zh" else EN_BOTTOM, "white", FONT_SMALL)
    canvas.paste(banner, (19, 19))

    bottom = Image.new("RGB", (1000, 182), "#FFF")
    button = Image.new("RGB", (283, 121), "#4790E4")
    draw = ImageDraw.Draw(button)
    draw.text(
        (100, 60),
        ("跳过" if language == "zh" else "SKIP"),
        "white", FONT_SMALL
    )
    bottom.paste(button, (687, 30))
    bottom_border = Image.new("RGB", (1002, 186), "#D5D5D5")
    bottom_border.paste(bottom, (2, 2))
    canvas.paste(bottom_border, (-2, 1353))

    bytes_io = BytesIO()
    res = Image.new("RGB", (1004, 1539), "#D5D5D5")
    res.paste(canvas, (2, 2))
    res.save(bytes_io, format="png")
    return bytes_io.getvalue()
