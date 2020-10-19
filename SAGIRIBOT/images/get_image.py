from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.functions import random_pic
from SAGIRIBOT.basics.get_config import get_config


async def get_pic(image_type: str) -> list:
    """
    Return random pics message

    Args:
        image_type: The type of picture to return
            image type list:
                setu: hPics(animate R-15)
                setu18: hPics(animate R-18)
                real: hPics(real person R-15)
                bizhi: Wallpaper(animate All age)

    Examples:
        assist_process = await get_pic("setu")[0]
        message = await get_pic("real")[1]

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    async def color() -> str:
        base_path = await get_config("setuPath")
        pic_path = await random_pic(base_path)
        return pic_path

    async def color18() -> str:
        base_path = await get_config("setu18Path")
        pic_path = await random_pic(base_path)
        return pic_path

    async def real() -> str:
        base_path = await get_config("realPath")
        pic_path = await random_pic(base_path)
        return pic_path

    async def wallpaper() -> str:
        base_path = await get_config("wallpaperPath")
        pic_path = await random_pic(base_path)
        return pic_path

    switch = {
        "setu": color(),
        "setu18": color18(),
        "real": real(),
        "bizhi": wallpaper()
    }

    target_pic_path = await switch[image_type]
    message = MessageChain.create([
        Image.fromLocalFile(target_pic_path)
    ])
    return ["None", message]
