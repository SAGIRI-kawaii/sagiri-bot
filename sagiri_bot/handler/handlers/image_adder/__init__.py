import re
import os
import aiohttp
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Union
from loguru import logger
from PIL import Image as IMG

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    FullMatch,
    RegexMatch,
    WildcardMatch,
    RegexResult,
)

from sagiri_bot.control import Permission
from sagiri_bot.config import GlobalConfig

saya = Saya.current()
channel = Channel.current()

channel.name("ImageAdder")
channel.author("SAGIRI-kawaii")
channel.description("一个能够在图库中添加图片的插件")

config = create(GlobalConfig)
image_paths: Dict[str, str] = config.image_path
legal_type = image_paths.keys()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("添加"),
                    RegexMatch(".*") @ "image_type_match",
                    FullMatch("图片"),
                    WildcardMatch().flags(re.DOTALL),
                ]
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN)],
    )
)
async def image_adder(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    source: Source,
    image_type_match: RegexResult,
):
    image_type: str = image_type_match.result.display.strip()
    if image_type not in legal_type:
        return await app.send_group_message(
            group,
            MessageChain(f"非法图片类型！\n合法image_type：{'、'.join(legal_type)}"),
            quote=source,
        )

    if not (path := image_paths.get(image_type)):
        return await app.send_group_message(
            group, MessageChain(f"无{image_type}项！请检查配置！"), quote=source
        )

    if os.path.exists(path):
        try:
            await add_image(path, message.get(Image))
        except:
            logger.exception("")
            return await app.send_group_message(
                group, MessageChain("出错了呐~请查看日志/控制台输出！")
            )
        await app.send_group_message(
            group, MessageChain(f"保存成功！共保存了{len(message.get(Image))}张图片！")
        )
    else:
        await app.send_group_message(
            group,
            MessageChain(
                [Image(path="statics/error/path_not_exists.png")]
            ),
            quote=source,
        )
        


async def add_image(path: Union[str, Path], images: List[Image]) -> None:
    path = Path(path)
    async with aiohttp.ClientSession() as session:
        for image in images:
            assert image.url is not None
            assert image.id is not None
            async with session.get(url=image.url) as resp:
                img_content = await resp.read()
            
            img_path = Path(image.id)
            img_path.with_stem(img_path.stem[1:-1])
            if img_path.suffix == ".mirai":
                img_path = img_path.with_suffix(".jpg")
            save_path = path / img_path
            save_path.write_bytes(img_content)
            logger.success(f"成功保存图片：{save_path}")
