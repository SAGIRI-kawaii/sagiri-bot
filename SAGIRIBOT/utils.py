import os
import io
import math
import yaml
import base64
import asyncio
import traceback
from io import BytesIO
from typing import Union
from loguru import logger
from PIL import ImageFont, ImageDraw
from PIL import Image as IMG
from sqlalchemy import select

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image, Image_LocalFile, Image_UnsafeBytes

from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.ORM.Tables import Setting, UserPermission, UserCalledCount

yaml.warnings({'YAMLLoadWarning': False})


class MessageChainUtils:
    @staticmethod
    async def messagechain_to_img(
        message: MessageChain,
        max_width: int = 1080,
        font_size: int = 40,
        spacing: int = 15,
        padding_x: int = 20,
        padding_y: int = 15,
        img_fixed: bool = False,
        font_path: str = f"{os.getcwd()}/statics/fonts/STKAITI.TTF",
    ) -> MessageChain:
        """
        将 MessageChain 转换为图片，仅支持只含有本地图片/文本的 MessageChain
        Args:
            message: 要转换的MessageChain
            max_width: 最大长度
            font_size: 字体尺寸
            spacing: 行间距
            padding_x: x轴距离边框大小
            padding_y: y轴距离边框大小
            img_fixed: 图片是否适应大小（仅适用于图片小于最大长度时）
            font_path: 字体文件路径
        Examples:
            msg = await messagechain_to_img(message=message)
        Returns:
            MessageChain （内含图片Image类）
        """

        def get_final_text_lines(text: str, text_width: int, font: ImageFont.FreeTypeFont) -> int:
            lines = text.split("\n")
            line_count = 0
            for line in lines:
                if not line:
                    line_count += 1
                    continue
                line_count += int(math.ceil(float(font.getsize(line)[0]) / float(text_width)))
            return line_count + 1

        font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
        message = message.asMerged()
        elements = message.__root__

        plains = message.get(Plain)
        text_gather = "\n".join([plain.text for plain in plains])
        # print(max(font.getsize(text)[0] for text in text_gather.split("\n")) + 2 * padding_x)
        final_width = min(max(font.getsize(text)[0] for text in text_gather.split("\n")) + 2 * padding_x, max_width)
        text_width = final_width - 2 * padding_x
        text_height = (font_size + spacing) * get_final_text_lines(text_gather, text_width, font)

        img_height_sum = 0
        temp_img_list = []
        images = [element for element in message.__root__ if (isinstance(element, Image_LocalFile) or isinstance(element, Image_UnsafeBytes))]
        for image in images:
            if isinstance(image, Image_LocalFile):
                temp_img = IMG.open(image.filepath)
            elif isinstance(image, Image_UnsafeBytes):
                temp_img = IMG.open(BytesIO(image.image_bytes))
            else:
                raise ValueError("messagechain_to_img：仅支持Image_LocalFile和Image_UnsafeBytes类的处理！")
            img_width, img_height = temp_img.size
            temp_img_list.append(
                temp_img := temp_img.resize((
                    int(final_width - 2 * spacing),
                    int(float(img_height * (final_width - 2 * spacing)) / float(img_width))
                )) if img_width > final_width - 2 * spacing or (img_fixed and img_width < final_width - 2 * spacing)
                else temp_img
            )
            img_height_sum = img_height_sum + temp_img.size[1]
        final_height = 2 * padding_y + text_height + img_height_sum
        picture = IMG.new('RGB', (final_width, final_height), (255, 255, 255))
        draw = ImageDraw.Draw(picture)
        present_x = padding_x
        present_y = padding_y
        image_index = 0
        for element in elements:
            if isinstance(element, Image) or isinstance(element, Image_UnsafeBytes) or isinstance(element, Image_LocalFile):
                picture.paste(temp_img_list[image_index], (present_x, present_y))
                present_y += (spacing + temp_img_list[image_index].size[1])
                image_index += 1
            elif isinstance(element, Plain):
                for char in element.text:
                    if char == "\n":
                        present_y += (font_size + spacing)
                        present_x = padding_x
                        continue
                    if char == "\r":
                        continue
                    if present_x + font.getsize(char)[0] > text_width:
                        present_y += (font_size + spacing)
                        present_x = padding_x
                    draw.text((present_x, present_y), char, font=font, fill=(0, 0, 0))
                    present_x += font.getsize(char)[0]
                present_y += (font_size + spacing)
                present_x = padding_x
        bytes_io = BytesIO()
        picture.save(bytes_io, format='PNG')
        logger.success("消息转图片处理成功！")
        return MessageChain.create([
            Image.fromUnsafeBytes(bytes_io.getvalue())
        ])


def load_configs() -> dict:
    pass


def sec_format(secs: int) -> str:
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return "%2d:%2d:%2d" % (h, m, s)


def get_config(config: str):
    """
    get config from config.json

    Args:
        config: Config name to query
            config list:
                BotQQ: Bot QQ number
                HostQQ: Host QQ number
                authKey: Authkey linked to mirai_http_api
                miraiHost: Host address of mirai_http_api
                dbHost: Host address of MySQL database
                dbName: Database name
                dbUser: Database account name
                dbPass: Database password of dbUser
                setuPath: HPics gallery path(animate)
                realPath: HPics gallery path(real person)

    Examples:
        get_config("BotQQ")

    Returns:
        Return parameter type list:
            BotQQ: int
            HostQQ: int
            authKey: str
            miraiHost: str
            dbHost: str
            dbName: str
            dbUser: str
            dbPass: str
            setuPath: str
    """
    with open('config.yaml', 'r', encoding='utf-8') as f:
        configs = yaml.load(f.read())
    if config in configs.keys():
        return configs[config]
    else:
        logger.error(f"getConfig Error: {config}")


async def get_setting(group_id: int, setting) -> Union[bool, str]:
    if result := list(orm.fetchone(select(setting).where(Setting.group_id == group_id))):
        return result[0][0]
    else:
        raise ValueError(f"未找到 {group_id} -> {str(setting)} 结果！请检查数据库！")


async def user_permission_require(group: Group, member: Member, level: int) -> bool:
    if result := list(orm.fetchone(
        select(
            UserPermission.level
        ).where(
            UserPermission.group_id == group.id,
            UserPermission.member_id == member.id
        )
    )):
        return True if result[0][0] >= level else False
    else:
        try:
            orm.add(UserPermission, {"group_id": group.id, "member_id": member.id, "level": 1})
        except Exception:
            logger.error(traceback.format_exc())
            orm.session.rollback()
        return True if level <= 1 else False


async def update_user_call_count_plus1(group: Group, member: Member, table_column, column_name: str) -> bool:
    new_value = list(orm.fetchone(
        select(table_column).where(UserCalledCount.group_id == group.id, UserCalledCount.member_id == member.id))
    )
    new_value = new_value[0][0] + 1 if new_value else 1
    try:
        orm.update(
            UserCalledCount,
            {"group_id": group.id, "member_id": member.id},
            {"group_id": group.id, "member_id": member.id, column_name: new_value}
        )
        return True
    except Exception:
        logger.error(traceback.format_exc())
        orm.session.rollback()
        return False


async def get_admins(group: Group) -> list:
    admins_res = list(orm.fetchall(
        select(
            UserPermission.member_id
        ).where(
            UserPermission.group_id == group.id,
            UserPermission.level > 1
        )
    ))
    admins = [item[0] for item in admins_res]
    return admins


async def online_notice(app: GraiaMiraiApplication):
    group_list = await app.groupList()
    for group in group_list:
        if await get_setting(group.id, Setting.online_notice):
            await app.sendGroupMessage(group, MessageChain.create([Plain(text="纱雾酱打卡上班啦！")]))


async def compress_image_bs4(b64, mb=100, k=0.9):
    """不改变图片尺寸压缩到指定大小
    :param outfile: 压缩文件保存地址
    :param mb: 压缩目标，KB
    :param step: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """
    f = base64.b64decode(b64)
    with io.BytesIO(f) as im:
        o_size = len(im.getvalue()) // 1024
        if o_size <= mb:
            return b64
        im_out = im
        while o_size > mb:
            img = IMG.open(im_out)
            x, y = img.size
            out = img.resize((int(x*k), int(y*k)), IMG.ANTIALIAS)
            im_out.close()
            im_out = io.BytesIO()
            out.save(im_out, 'jpeg')
            o_size = len(im_out.getvalue()) // 1024
        b64 = base64.b64encode(im_out.getvalue())
        im_out.close()
        return str(b64, encoding='utf8')


def sec_to_str(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def single_task(handle_func, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    asyncio.run_coroutine_threadsafe(handle_func(app, message, group, member), AppCore.get_core_instance().get_loop())
