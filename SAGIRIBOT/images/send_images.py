from SAGIRIBOT.images.get_image import get_pic
from graia.application import GraiaMiraiApplication


async def send_images(app: GraiaMiraiApplication, group_id: int, image_type: str):
    msg = await get_pic(image_type)
    source = app.sendGroupMessage(group_id, msg[1])
    return [msg[0], source]
