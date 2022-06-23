import os
import re
import numpy
import random
import aiohttp
import imageio
import hashlib
from io import BytesIO
from typing import Union
from PIL import Image as IMG
from moviepy.editor import ImageSequenceClip
from PIL import ImageDraw, ImageFilter, ImageOps

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import At, Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import RegexMatch, ElementMatch, RegexResult, ElementResult

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


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


saya = Saya.current()
channel = Channel.current()

channel.name("AvatarFunPic")
channel.author("SAGIRI-kawaii")
channel.description("一个可以生成头像相关趣味图的插件，在群中发送 `[摸|亲|贴|撕|丢|爬|精神支柱|吞] [@目标|目标qq|目标图片]` 即可")


@channel.use(ListenerSchema(
    listening_events=[GroupMessage],
    inline_dispatchers=[
        Twilight([
            RegexMatch("(摸|亲|贴|撕|丢|爬|精神支柱|吞)") @ "cmd",
            ElementMatch(At, optional=True) @ "at1",
            ElementMatch(At, optional=True) @ "at2",
            RegexMatch(r"[0-9]+", optional=True) @ "qq1",
            RegexMatch(r"[0-9]+", optional=True) @ "qq2",
            ElementMatch(Image, optional=True) @ "img1",
            ElementMatch(Image, optional=True) @ "img2"
        ])
    ],
    decorators=[
        FrequencyLimit.require("avatar_fun_pic", 1),
        Function.require(channel.module, notice=True),
        BlackListControl.enable(),
        UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
    ]
))
async def avatar_fun_pic(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    cmd: RegexResult,
    at1: ElementResult,
    at2: ElementResult,
    qq1: RegexResult,
    qq2: RegexResult,
    img1: ElementResult,
    img2: ElementResult
):
    if result := await AvatarFunPic.handle(app, message, group, member, cmd, at1, at2, qq1, qq2, img1, img2):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class AvatarFunPic(AbstractHandler):
    __name__ = "AvatarFunPic"
    __description__ = "一个可以生成头像相关趣味图的插件"
    __usage__ = "在群中发送 `[摸|亲|贴|撕|丢|爬|精神支柱|吞] [@目标|目标qq|目标图片]` 即可"

    @staticmethod
    def get_match_element(message: MessageChain) -> list:
        return [element for element in message.__root__ if isinstance(element, Image) or isinstance(element, At)]

    @staticmethod
    @switch()
    @blacklist()
    async def handle(
        app: Ariadne,
        message: MessageChain,
        group: Group,
        member: Member,
        cmd: RegexResult,
        at1: ElementResult,
        at2: ElementResult,
        qq1: RegexResult,
        qq2: RegexResult,
        img1: ElementResult,
        img2: ElementResult
    ):
        if not any([at1.matched, at2.matched, qq1.matched, qq2.matched, img1.matched, img2.matched]):
            return None
        await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
        message_text = message.asDisplay()
        if message_text.startswith("摸"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) >= 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.petpet(element.target if isinstance(element, At) else element.url)
            elif re.match(r"摸 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.petpet(int(message_text[2:]))

        elif message_text.startswith("亲"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) == 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.kiss(
                    member.id, 
                    element.target if isinstance(element, At) else element.url
                )
            elif len(match_elements) > 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element1 = match_elements[0]
                element2 = match_elements[1]
                return await AvatarFunPic.kiss(
                    element1.target if isinstance(element1, At) else element1.url,
                    element2.target if isinstance(element2, At) else element2.url
                )
            elif re.match(r"亲 [0-9]+ [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                operator, target = message_text[2:].split(" ")
                return await AvatarFunPic.kiss(int(operator), int(target))
            elif re.match(r"亲 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.kiss(member.id, int(message_text[2:]))

        elif message_text.startswith("贴"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) == 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.rub(
                    member.id, 
                    element.target if isinstance(element, At) else element.url
                )
            elif len(match_elements) > 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element1 = match_elements[0]
                element2 = match_elements[1]
                return await AvatarFunPic.rub(
                    element1.target if isinstance(element1, At) else element1.url,
                    element2.target if isinstance(element2, At) else element2.url
                )
            elif re.match(r"贴 [0-9]+ [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                operator, target = message_text[2:].split(" ")
                return await AvatarFunPic.rub(int(operator), int(target))
            elif re.match(r"贴 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.rub(member.id, int(message_text[2:]))

        elif message_text.startswith("撕"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) >= 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.ripped(element.target if isinstance(element, At) else element.url)
            elif re.match(r"撕 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.ripped(int(message_text[2:]))

        elif message_text.startswith("丢"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) >= 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.throw(element.target if isinstance(element, At) else element.url)
            elif re.match(r"丢 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.throw(int(message_text[2:]))

        elif message_text.startswith("爬"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) >= 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.crawl(element.target if isinstance(element, At) else element.url)
            elif re.match(r"爬 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.crawl(int(message_text[2:]))

        elif message_text.startswith("精神支柱"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) >= 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.support(element.target if isinstance(element, At) else element.url)
            elif re.match(r"精神支柱 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.support(int(message_text[5:]))

        elif message_text.startswith("吞"):
            match_elements = AvatarFunPic.get_match_element(message)
            if len(match_elements) >= 1:
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                element = match_elements[0]
                return await AvatarFunPic.swallowed(element.target if isinstance(element, At) else element.url)
            elif re.match(r"吞 [0-9]+", message_text):
                await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
                return await AvatarFunPic.swallowed(int(message_text[2:]))
        else:
            return None

    @staticmethod
    async def get_pil_avatar(image: Union[int, str]):
        if isinstance(image, int):
            url = f'http://q1.qlogo.cn/g?b=qq&nk={str(image)}&s=640'
        else:
            url = image
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                img_content = await resp.read()

        return IMG.open(BytesIO(img_content)).convert("RGBA")

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
    async def petpet(image: Union[int, str], flip=False, squish=0, fps=20) -> MessageItem:
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

        avatar = await AvatarFunPic.get_pil_avatar(image)

        # 生成每一帧
        for i in range(5):
            gif_frames.append(await AvatarFunPic.make_frame(avatar, i, squish=squish, flip=flip))

        if not os.path.exists(f"{os.getcwd()}/statics/temp/"):
            os.mkdir(f"{os.getcwd()}/statics/temp/")
        md5 = hashlib.md5(str(image).encode("utf-8")).hexdigest()
        await AvatarFunPic.save_gif(gif_frames, f"{os.getcwd()}/statics/temp/tempPetPet-{md5}.gif", fps=fps)

        with open(f"{os.getcwd()}/statics/temp/tempPetPet-{md5}.gif", "rb") as r:
            image_bytes = r.read()

        os.remove(f"{os.getcwd()}/statics/temp/tempPetPet-{md5}.gif")

        return MessageItem(MessageChain.create([Image(data_bytes=image_bytes)]), Normal())

    @staticmethod
    async def kiss_make_frame(operator, target, i):
        target = target.convert('RGBA')
        operator = operator.convert('RGBA')
        operator_x = [92, 135, 84, 80, 155, 60, 50, 98, 35, 38, 70, 84, 75]
        operator_y = [64, 40, 105, 110, 82, 96, 80, 55, 65, 100, 80, 65, 65]
        target_x = [58, 62, 42, 50, 56, 18, 28, 54, 46, 60, 35, 20, 40]
        target_y = [90, 95, 100, 100, 100, 120, 110, 100, 100, 100, 115, 120, 96]
        bg = IMG.open(f"{os.getcwd()}/statics/KissKissFrames/{i}.png")
        gif_frame = IMG.new('RGBA', (200, 200), (255, 255, 255))
        gif_frame.paste(bg, (0, 0))
        gif_frame.paste(target, (target_x[i - 1], target_y[i - 1]), target)
        gif_frame.paste(operator, (operator_x[i - 1], operator_y[i - 1]), operator)
        return numpy.array(gif_frame)

    @staticmethod
    async def kiss(operator_image: Union[int, str], target_image: Union[int, str]) -> MessageItem:
        """
        Author: https://github.com/SuperWaterGod
        """
        gif_frames = []
        operator = await AvatarFunPic.get_pil_avatar(operator_image)
        target = await AvatarFunPic.get_pil_avatar(target_image)

        operator = operator.resize((40, 40), IMG.ANTIALIAS)
        size = operator.size
        r2 = min(size[0], size[1])
        circle = IMG.new('L', (r2, r2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, r2, r2), fill=255)
        alpha = IMG.new('L', (r2, r2), 255)
        alpha.paste(circle, (0, 0))
        operator.putalpha(alpha)

        target = target.resize((50, 50), IMG.ANTIALIAS)
        size = target.size
        r2 = min(size[0], size[1])
        circle = IMG.new('L', (r2, r2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, r2, r2), fill=255)
        alpha = IMG.new('L', (r2, r2), 255)
        alpha.paste(circle, (0, 0))
        target.putalpha(alpha)

        md5 = hashlib.md5(str(str(operator_image) + str(target_image)).encode("utf-8")).hexdigest()
        for i in range(1, 14):
            gif_frames.append(await AvatarFunPic.kiss_make_frame(operator, target, i))
        await AvatarFunPic.save_gif(gif_frames, f"{os.getcwd()}/statics/temp/tempKiss-{md5}.gif", fps=25)
        with open(f"{os.getcwd()}/statics/temp/tempKiss-{md5}.gif", 'rb') as r:
            img_content = r.read()
        os.remove(f"{os.getcwd()}/statics/temp/tempKiss-{md5}.gif")
        return MessageItem(MessageChain.create([Image(data_bytes=img_content)]), Normal())

    @staticmethod
    async def ripped(image: Union[int, str]) -> MessageItem:
        ripped = IMG.open(f"{os.getcwd()}/statics/ripped.png")
        frame = IMG.new('RGBA', (1080, 804), (255, 255, 255, 0))
        avatar = await AvatarFunPic.get_pil_avatar(image)
        left = avatar.resize((385, 385)).rotate(24, expand=True)
        right = avatar.resize((385, 385)).rotate(-11, expand=True)
        frame.paste(left, (-5, 355))
        frame.paste(right, (649, 310))
        frame.paste(ripped, mask=ripped)
        frame = frame.convert('RGB')
        output = BytesIO()
        frame.save(output, format='jpeg')
        return MessageItem(MessageChain.create([Image(data_bytes=output.getvalue())]), Normal())

    @staticmethod
    async def throw(image: Union[int, str]) -> MessageItem:
        avatar = await AvatarFunPic.get_pil_avatar(image)
        mask = IMG.new('L', avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        offset = 1
        draw.ellipse((offset, offset, avatar.size[0] - offset, avatar.size[1] - offset),
                     fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        avatar.putalpha(mask)
        avatar = avatar.rotate(random.randint(1, 360), IMG.BICUBIC)
        avatar = avatar.resize((143, 143), IMG.ANTIALIAS)
        throw = IMG.open(f"{os.getcwd()}/statics/throw.png")
        throw.paste(avatar, (15, 178), mask=avatar)
        throw = throw.convert('RGB')
        output = BytesIO()
        throw.save(output, format='jpeg')
        return MessageItem(MessageChain.create([Image(data_bytes=output.getvalue())]), Normal())

    @staticmethod
    async def crawl(image: Union[int, str]) -> MessageItem:
        avatar = await AvatarFunPic.get_pil_avatar(image)
        mask = IMG.new('L', avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        offset = 1
        draw.ellipse((offset, offset, avatar.size[0] - offset, avatar.size[1] - offset),
                     fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        avatar.putalpha(mask)
        images = [i for i in os.listdir(f"{os.getcwd()}/statics/crawl")]
        crawl = IMG.open(f"{os.getcwd()}/statics/crawl/{random.choice(images)}").resize(
            (500, 500), IMG.ANTIALIAS)
        avatar = avatar.resize((100, 100), IMG.ANTIALIAS)
        crawl.paste(avatar, (0, 400), mask=avatar)
        crawl = crawl.convert('RGB')
        output = BytesIO()
        crawl.save(output, format='jpeg')
        return MessageItem(MessageChain.create([Image(data_bytes=output.getvalue())]), Normal())

    @staticmethod
    async def resize_img(img, width, height, angle=0):
        mask = IMG.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        img.putalpha(mask)
        img = img.resize((width, height), IMG.ANTIALIAS)
        if angle:
            img = img.rotate(angle, IMG.BICUBIC, expand=True)
        return img

    @staticmethod
    async def rub(operator_image: Union[int, str], target_image: Union[int, str]) -> MessageItem:
        user_locs = [(39, 91, 75, 75, 0), (49, 101, 75, 75, 0), (67, 98, 75, 75, 0),
                     (55, 86, 75, 75, 0), (61, 109, 75, 75, 0), (65, 101, 75, 75, 0)]
        self_locs = [(102, 95, 70, 80, 0), (108, 60, 50, 100, 0), (97, 18, 65, 95, 0),
                     (65, 5, 75, 75, -20), (95, 57, 100, 55, -70), (109, 107, 65, 75, 0)]
        frames = []
        self_img = await AvatarFunPic.get_pil_avatar(operator_image)
        user_img = await AvatarFunPic.get_pil_avatar(target_image)
        for i in range(6):
            frame = IMG.open(f'{os.getcwd()}/statics/RubFrames/frame{i}.png').convert('RGBA')
            x, y, w, h, angle = user_locs[i]
            user_img_new = (await AvatarFunPic.resize_img(user_img, w, h, angle)).convert("RGBA")
            frame.paste(user_img_new, (x, y), mask=user_img_new)
            x, y, w, h, angle = self_locs[i]
            self_img_new = (await AvatarFunPic.resize_img(self_img, w, h, angle)).convert("RGBA")
            frame.paste(self_img_new, (x, y), mask=self_img_new)
            frames.append(frame)
        output = BytesIO()
        imageio.mimsave(output, frames, format='gif', duration=0.05)
        return MessageItem(MessageChain.create([Image(data_bytes=output.getvalue())]), Normal())

    @staticmethod
    async def support(image: Union[int, str]) -> MessageItem:
        avatar = await AvatarFunPic.get_pil_avatar(image)
        support = IMG.open(f'{os.getcwd()}/statics/support.png')
        frame = IMG.new('RGBA', (1293, 1164), (255, 255, 255, 0))
        avatar = avatar.resize((815, 815), IMG.ANTIALIAS).rotate(23, expand=True)
        frame.paste(avatar, (-172, -17))
        frame.paste(support, mask=support)
        frame = frame.convert('RGB')
        output = BytesIO()
        frame.save(output, format='jpeg')
        return MessageItem(MessageChain.create([Image(data_bytes=output.getvalue())]), Normal())

    @staticmethod
    async def swallowed(image: Union[int, str]) -> MessageItem:
        avatar = await AvatarFunPic.get_pil_avatar(image)
        frame_locs = [(180, 60, 100, 100), (184, 75, 100, 100),
                      (183, 98, 100, 100), (179, 118, 110, 100),
                      (156, 194, 150, 48), (178, 136, 122, 69),
                      (175, 66, 122, 85), (170, 42, 130, 96),
                      (175, 34, 118, 95), (179, 35, 110, 93),
                      (180, 54, 102, 93), (183, 58, 97, 92),
                      (174, 35, 120, 94), (179, 35, 109, 93),
                      (181, 54, 101, 92), (182, 59, 98, 92),
                      (183, 71, 90, 96), (180, 131, 92, 101)]
        raw_frames = [f"{os.getcwd()}/statics/SwallowedFrames/frame{i}.png" for i in range(23)]
        raw_frames = [IMG.open(i).convert('RGBA') for i in raw_frames]

        avatar_frames = []
        for i in range(len(frame_locs)):
            frame = IMG.new('RGBA', (480, 400), (255, 255, 255, 0))
            x, y, l, w = frame_locs[i]
            avatar_resized = avatar.resize((l, w), IMG.ANTIALIAS)
            frame.paste(avatar_resized, (x, y))
            img = raw_frames[i]
            frame.paste(img, mask=img)
            avatar_frames.append(frame)

        frames = []
        for i in range(2):
            frames.extend(avatar_frames[0:12])
        frames.extend(avatar_frames[0:8])
        frames.extend(avatar_frames[12:18])
        frames.extend(raw_frames[18:23])

        output = BytesIO()
        imageio.mimsave(output, frames, format='gif', duration=0.06)
        return MessageItem(MessageChain.create([Image(data_bytes=output.getvalue())]), Normal())

