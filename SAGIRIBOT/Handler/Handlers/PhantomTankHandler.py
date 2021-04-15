import aiohttp
import numpy as np
from io import BytesIO
from PIL import Image as IMG

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount


class PhantomTankHandler(AbstractHandler):
    __name__ = "PhantomTankHandler"
    __description__ = "一个幻影坦克生成器Handler"
    __usage__ = "在群中发送 `幻影 [显示图] [隐藏图]` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = "".join([plain.text for plain in message.get(Plain)]).strip()
        if message_text == "幻影" or message_text == "彩色幻影":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            if len(message.get(Image)) != 2:
                set_result(message, MessageItem(
                    MessageChain.create([Plain(text="非预期图片数！请按照 `显示图 隐藏图` 顺序发送，一共两张图片")]),
                    QuoteSource(GroupStrategy())
                ))
                # return MessageItem(
                #     MessageChain.create([Plain(text="非预期图片数！请按照 `显示图 隐藏图` 顺序发送，一共两张图片")]),
                #     QuoteSource(GroupStrategy())
                # )
            else:
                display_img = message[Image][0]
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=display_img.url) as resp:
                        display_img = IMG.open(BytesIO(await resp.read()))

                hide_img = message[Image][1]
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=hide_img.url) as resp:
                        hide_img = IMG.open(BytesIO(await resp.read()))

                set_result(message, await self.get_message(group, member, display_img, hide_img))
                # return await self.get_message(group, member, display_img, hide_img)
        else:
            return None
            # return await super().handle(app, message, group, member)

    @staticmethod
    @frequency_limit_require_weight_free(2)
    async def get_message(group: Group, member: Member, display_img: IMG, hide_img: IMG):
        return MessageItem(
            MessageChain.create([Image.fromUnsafeBytes(await PhantomTankHandler.make_tank(display_img, hide_img))]),
            QuoteSource(GroupStrategy())
        )

    @staticmethod
    def get_max_size(a, b):
        return a if a[0] * a[1] >= b[0] * b[1] else b

    @staticmethod
    async def make_tank(im_1: IMG, im_2: IMG) -> bytes:
        im_1 = im_1.convert("L")
        im_2 = im_2.convert("L")
        max_size = PhantomTankHandler.get_max_size(im_1.size, im_2.size)
        if max_size == im_1.size:
            im_2 = im_2.resize(max_size)
        else:
            im_1 = im_1.resize(max_size)
        arr_1 = np.array(im_1, dtype=np.uint8)
        arr_2 = np.array(im_2, dtype=np.uint8)
        arr_1 = 225 - 70 * ((np.max(arr_1) - arr_1) / (np.max(arr_1) - np.min(arr_1)))
        arr_2 = 30 + 70 * ((arr_2 - np.min(arr_2)) / (np.max(arr_2) - np.min(arr_2)))
        arr_alpha = 255 - (arr_1 - arr_2)
        arr_offset = arr_2 * (255 / arr_alpha)
        arr_new = np.dstack([arr_offset, arr_alpha]).astype(np.uint8)
        if arr_new.shape[0] == 3:
            arr_new = (np.transpose(arr_new, (1, 2, 0)) + 1) / 2.0 * 255.0
        bytesIO = BytesIO()
        IMG.fromarray(arr_new).save(bytesIO, format='PNG')
        return bytesIO.getvalue()
