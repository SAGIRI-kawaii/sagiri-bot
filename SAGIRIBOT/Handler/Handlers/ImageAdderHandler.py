import re
import os
import aiohttp
import traceback
from io import BytesIO
from loguru import logger
from PIL import Image as IMG

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal, QuoteSource
from SAGIRIBOT.utils import get_config, get_image_save_number, user_permission_require

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def image_adder_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await ImageAdderHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class ImageAdderHandler(AbstractHandler):
    __name__ = "ImageAdderHandler"
    __description__ = "一个能够在群中添加图片的handler"
    __usage__ = "在群中发送 `添加(setu|setu18|real|realHighq|wallpaper|sketch)图片[图片]` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        legal_type = ("setu", "setu18", "real", "realHighq", "wallpaper", "sketch")
        if re.match(r"添加(setu|setu18|real|realHighq|wallpaper|sketch)图片(\[图片])+", message.asDisplay()):
            if not user_permission_require(group, member, 2):
                return MessageItem(MessageChain.create([Plain(text="你没有权限，爬！")]), Normal(GroupStrategy()))
            image_type = re.findall(r"添加(.*?)图片.*(\[图片].*)+", message.asDisplay(), re.S)[0][0]
            if image_type not in legal_type:
                return MessageItem(
                    MessageChain.create([Plain(text=f"非法图片类型！\n合法image_type：{'、'.join(legal_type)}")]),
                    QuoteSource(GroupStrategy())
                )
            if path := get_config(f"{image_type}Path"):
                if os.path.exists(path):
                    try:
                        await ImageAdderHandler.add_image(path, message.get(Image))
                    except:
                        logger.error(traceback.format_exc())
                        return MessageItem(MessageChain.create([Plain(text="出错了呐~请查看日志/控制台输出！")]), Normal(GroupStrategy()))
                    return MessageItem(
                        MessageChain.create([Plain(text=f"保存成功！共保存了{len(message.get(Image))}张图片！")]),
                        Normal(GroupStrategy())
                    )
                else:
                    return MessageItem(
                        MessageChain.create(
                            [Image.fromLocalFile(f"{os.getcwd()}/statics/error/path_not_exists.png")]),
                        QuoteSource(GroupStrategy())
                    )
            else:
                return MessageItem(
                    MessageChain.create([Plain(text=f"无{image_type}Path项！请检查配置！")]),
                    QuoteSource(GroupStrategy())
                )
        else:
            return None

    @staticmethod
    async def add_image(path: str, images: list):
        for image in images:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=image.url) as resp:
                    img_content = await resp.read()
            img_suffix = image.imageId.split('.').pop()
            img_suffix = img_suffix if img_suffix != 'mirai' else 'png'
            img = IMG.open(BytesIO(img_content))
            # save_path = os.path.join(path, f"{get_image_save_number()}.{img_suffix}")
            save_path = os.path.join(path, f"{image.imageId.split('.')[0][1:-1]}.{img_suffix}")
            # while os.path.exists(save_path):
            #     save_path = os.path.join(path, f"{get_image_save_number()}.{img_suffix}")
            img.save(save_path)
