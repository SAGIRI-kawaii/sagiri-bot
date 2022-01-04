import re
import os
import aiohttp
import traceback
from io import BytesIO
from typing import List
from loguru import logger
from PIL import Image as IMG

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.utils import user_permission_require
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.strategy import Normal, QuoteSource
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("ImageAdder")
channel.author("SAGIRI-kawaii")
channel.description("一个能够在图库中添加图片的插件")

core = AppCore.get_core_instance()
image_paths = core.get_config().image_path
legal_type = image_paths.keys()
pattern = r"添加(" + '|'.join([key for key in legal_type]) + r")图片.*(\[图片])+"


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def image_adder(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await ImageAdder.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class ImageAdder(AbstractHandler):
    __name__ = "ImageAdderHandler"
    __description__ = "一个能够在图库中添加图片的插件"
    __usage__ = "在群中发送 `添加(图库名)图片([图片])+` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(pattern, message.asDisplay()):
            if not await user_permission_require(group, member, 2):
                return MessageItem(MessageChain.create([Plain(text="你没有权限，爬！")]), Normal())
            image_type = re.findall(r"添加(.*?)图片.*(\[图片].*)+", message.asDisplay(), re.S)[0][0]
            if image_type not in legal_type:
                return MessageItem(
                    MessageChain.create([Plain(text=f"非法图片类型！\n合法image_type：{'、'.join(legal_type)}")]),
                    QuoteSource()
                )
            if path := image_paths.get(image_type):
                if os.path.exists(path):
                    try:
                        await ImageAdder.add_image(path, message.get(Image))
                    except:
                        logger.error(traceback.format_exc())
                        return MessageItem(MessageChain.create([Plain(text="出错了呐~请查看日志/控制台输出！")]), Normal())
                    return MessageItem(
                        MessageChain.create([Plain(text=f"保存成功！共保存了{len(message.get(Image))}张图片！")]),
                        Normal()
                    )
                else:
                    return MessageItem(
                        MessageChain.create(
                            [Image(path=f"{os.getcwd()}/statics/error/path_not_exists.png")]),
                        QuoteSource()
                    )
            else:
                return MessageItem(
                    MessageChain.create([Plain(text=f"无{image_type}项！请检查配置！")]),
                    QuoteSource()
                )
        else:
            return None

    @staticmethod
    async def add_image(path: str, images: List[Image]) -> None:
        for image in images:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=image.url) as resp:
                    img_content = await resp.read()
            img_suffix = image.id.split('.').pop()
            img_suffix = img_suffix if img_suffix != 'mirai' else 'png'
            img = IMG.open(BytesIO(img_content))
            # save_path = os.path.join(path, f"{get_image_save_number()}.{img_suffix}")
            save_path = os.path.join(path, f"{image.id.split('.')[0][1:-1]}.{img_suffix}")
            # while os.path.exists(save_path):
            #     save_path = os.path.join(path, f"{get_image_save_number()}.{img_suffix}")
            img.save(save_path)
            logger.success(f"成功保存图片：{save_path}")
