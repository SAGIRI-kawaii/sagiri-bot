import qrcode

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Image


async def make_qrcode(content: str) -> list:
    img = qrcode.make(content)
    img.save("./statics/temp/tempQrcodeMaked.jpg")
    return [
        "quoteSource",
        MessageChain.create([
            Image.fromLocalFile("./statics/temp/tempQrcodeMaked.jpg")
        ])
    ]