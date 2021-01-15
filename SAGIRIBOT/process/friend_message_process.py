import aiohttp
from PIL import Image as IMG
from io import BytesIO

from graia.application import GraiaMiraiApplication
from graia.application.friend import Friend
from graia.application.event.messages import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.exceptions import AccountMuted

from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.data_manage.get_data.get_total_calls import get_total_calls
from SAGIRIBOT.data_manage.update_data.update_total_calls import update_total_calls
from SAGIRIBOT.basics.write_log import write_log
from SAGIRIBOT.data_manage.update_data.insert_image_hash import insert_image_hash
from SAGIRIBOT.images.image_hash import image_hash


async def friend_message_process(app: GraiaMiraiApplication, friend: Friend, message: MessageChain) -> None:
    message_test = message.asDisplay()
    if friend.id == await get_config("HostQQ"):
        if message_test[:5] == "发布消息：":
            msg = MessageChain.create([
                Plain(text=message_test[5:])
            ])
            group_list = await app.groupList()
            for i in group_list:
                try:
                    await app.sendGroupMessage(i, msg)
                except AccountMuted:
                    pass
        elif message.has(Image):
            imgs = message.get(Image)
            for i in imgs:
                bot_setu_count = await get_total_calls("botSetuCount") + 1
                await update_total_calls(bot_setu_count, "botSetuCount")
                path = "%s%s.png" % (await get_config("listenImagePath"), bot_setu_count)

                async with aiohttp.ClientSession() as session:
                    async with session.get(url=i.url) as resp:
                        img_content = await resp.read()

                image = IMG.open(BytesIO(img_content))
                image.save(path)

                await insert_image_hash("%s%d.png" % (await get_config("listenImagePath"), bot_setu_count),
                                        await image_hash(path),
                                        "tribute"
                                    )
            await app.sendFriendMessage(friend, MessageChain.create([
                    Plain(text="%d Image saved!" % len(imgs))
                ]))
            await write_log("save img from Host", path, await get_config("HostQQ"), 0, True, "img")
