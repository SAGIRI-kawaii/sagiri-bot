import os
import numpy
import aiohttp
from io import BytesIO
from PIL import ImageOps
from PIL import Image as IMG
from moviepy.editor import ImageSequenceClip

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import Image

from SAGIRIBOT.MessageSender.Strategy import Normal
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount


frame_spec = [
    (27, 31, 86, 90),
    (22, 36, 91, 90),
    (18, 41, 95, 90),
    (22, 41, 91, 91),
    (27, 28, 86, 91)
]

squish_factor = [
    (0, 0, 0, 0),
    (-7, 22, 8, 0),
    (-8, 30, 9, 6),
    (-3, 21, 5, 9),
    (0, 0, 0, 0)
]

squish_translation_factor = [0, 20, 34, 21, 0]

frames = tuple([f'{os.getcwd()}/statics/PetPetFrames/frame{i}.png' for i in range(5)])


class AvatarFunPicHandler(AbstractHandler):
    __name__ = "AvatarFunPicHandler"
    __description__ = "一个可以生成头像相关趣味图的Handler"
    __usage__ = "在群中发送 `摸 @目标` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message.has(At) and message_text.startswith("摸"):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.petpet(message.get(At)[0].target))
            # return await self.petpet(message.get(At)[0].target)
        else:
            return None
            # return await super().handle(app, message, group, member)

    @staticmethod
    async def climb(member_id: int) -> MessageItem:
        url = f'http://q1.qlogo.cn/g?b=qq&nk={str(member_id)}&s=640'
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                img_content = await resp.read()

        avatar = IMG.open(BytesIO(img_content))
        pass

    @staticmethod
    async def save_gif(gif_frames, dest, fps=10):
        """生成 gif
        将输入的帧数据合并成视频并输出为 gif
        参数
        gif_frames: list<numpy.ndarray>
        为每一帧的数据
        dest: str
        为输出路径
        fps: int, float
        为输出 gif 每秒显示的帧数
        返回
        None
        但是会输出一个符合参数的 gif
        """
        clip = ImageSequenceClip(gif_frames, fps=fps)
        clip.write_gif(dest)  # 使用 imageio
        clip.close()

    @staticmethod
    async def make_frame(avatar, i, squish=0, flip=False):
        """生成帧
        将输入的头像转变为参数指定的帧，以供 make_gif() 处理
        参数
        avatar: PIL.Image.Image
        为头像
        i: int
        为指定帧数
        squish: float
        为一个 [0, 1] 之间的数，为挤压量
        flip: bool
        为是否横向反转头像
        返回
        numpy.ndarray
        为处理完的帧的数据
        """
        # 读入位置
        spec = list(frame_spec[i])
        # 将位置添加偏移量
        for j, s in enumerate(spec):
            spec[j] = int(s + squish_factor[i][j] * squish)
        # 读取手
        hand = IMG.open(frames[i])
        # 反转
        if flip:
            avatar = ImageOps.mirror(avatar)
        # 将头像放缩成所需大小
        avatar = avatar.resize((int((spec[2] - spec[0]) * 1.2), int((spec[3] - spec[1]) * 1.2)), IMG.ANTIALIAS)
        # 并贴到空图像上
        gif_frame = IMG.new('RGB', (112, 112), (255, 255, 255))
        gif_frame.paste(avatar, (spec[0], spec[1]))
        # 将手覆盖（包括偏移量）
        gif_frame.paste(hand, (0, int(squish * squish_translation_factor[i])), hand)
        # 返回
        return numpy.array(gif_frame)

    @staticmethod
    async def petpet(member_id: int, flip=False, squish=0, fps=20) -> MessageItem:
        """生成PetPet
        将输入的头像生成为所需的 PetPet 并输出
        参数
        path: str
        为头像路径
        flip: bool
        为是否横向反转头像
        squish: float
        为一个 [0, 1] 之间的数，为挤压量
        fps: int
        为输出 gif 每秒显示的帧数
        返回
        bool
        但是会输出一个符合参数的 gif
        """

        gif_frames = []

        url = f'http://q1.qlogo.cn/g?b=qq&nk={str(member_id)}&s=640'
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                img_content = await resp.read()

        avatar = IMG.open(BytesIO(img_content))

        # 生成每一帧
        for i in range(5):
            gif_frames.append(await AvatarFunPicHandler.make_frame(avatar, i, squish=squish, flip=flip))

        if not os.path.exists(f"{os.getcwd()}/statics/temp/"):
            os.mkdir(f"{os.getcwd()}/statics/temp/")

        await AvatarFunPicHandler.save_gif(gif_frames, f"{os.getcwd()}/statics/temp/tempPetPet-{member_id}.gif", fps=fps)

        with open(f"{os.getcwd()}/statics/temp/tempPetPet-{member_id}.gif", "rb") as r:
            image_bytes = r.read()

        os.remove(f"{os.getcwd()}/statics/temp/tempPetPet-{member_id}.gif")

        return MessageItem(MessageChain.create([Image.fromUnsafeBytes(image_bytes)]), Normal(GroupStrategy()))
