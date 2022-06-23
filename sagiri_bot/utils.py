import os
import io
import math
import yaml
import json
import base64
import aiohttp
import asyncio
import datetime
from io import BytesIO
from pathlib import Path
from loguru import logger
from PIL import Image as IMG
from sqlalchemy import select, column
from PIL import ImageDraw, ImageFont, ImageFilter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import InstrumentedAttribute
from typing import Tuple, Optional, Union, List, Literal, Dict

from graia.ariadne.app import Ariadne
from graia.ariadne.exception import AccountMuted
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.event.message import Group, Member, Friend

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.config import GlobalConfig
from sagiri_bot.orm.async_orm import Setting, UserPermission, UserCalledCount, FunctionCalledRecord

yaml.warnings({'YAMLLoadWarning': False})


class GroupSetting(object):
    data: Dict[int, Dict[str, Union[bool, str]]]

    def __init__(self):
        self.data = {}

    async def data_init(self):
        columns = {
            i: Setting.__dict__[i]
            for i in Setting.__dict__.keys() if isinstance(Setting.__dict__[i], InstrumentedAttribute)
        }
        column_names = list(columns.keys())
        column_names.sort()
        datas = await orm.fetchall(
            select(
                Setting.group_id,
                *([columns[name] for name in column_names])
            )
        )
        for data in datas:
            self.data[data[0]] = dict(zip(column_names, data[1:]))

    async def get_setting(self, group: Union[Group, int], setting: InstrumentedAttribute) -> Union[bool, str]:
        setting_name = str(setting).split('.')[1]
        if isinstance(group, Group):
            group = group.id
        if self.data.get(group, None):
            if res := self.data[group].get(setting_name):
                return res
        else:
            self.data[group] = {}
        if result := await orm.fetchone(select(setting).where(Setting.group_id == group)):
            self.data[group][setting_name] = result[0]
            return result[0]
        else:
            raise ValueError(f"未找到 {group} -> {str(setting)} 结果！请检查数据库！")

    async def modify_setting(
        self, group: Union[Group, int], setting: Union[InstrumentedAttribute, str], new_value: Union[bool, str]
    ):
        setting_name = str(setting).split('.')[1] if isinstance(setting, InstrumentedAttribute) else setting
        print("modify:", setting_name)
        if isinstance(group, Group):
            group = group.id
        if self.data.get(group, None):
            self.data[group][setting_name] = new_value
        else:
            self.data[group] = {setting_name: new_value}


group_setting = GroupSetting()


def sec_format(secs: int) -> str:
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return "%2d:%2d:%2d" % (h, m, s)


def get_config(config: str):
    """
    get config from config.json

    Args:
        config: Config name to query

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
        configs = yaml.load(f.read(), yaml.BaseLoader)
    if config in configs.keys():
        return configs[config]
    else:
        logger.error(f"getConfig Error: {config}")
        return None


async def get_setting(group: Union[Group, int], setting) -> Union[bool, str]:
    if isinstance(group, Group):
        group = group.id
    setting = str(setting).split(".", maxsplit=1)[1]
    if result := await orm.fetchone(select(column(setting)).where(Setting.group_id == group)):
        return result[0]
    else:
        raise ValueError(f"未找到 {group} -> {str(setting)} 结果！请检查数据库！")


async def update_user_call_count_plus(
        group: Group,
        member: Member,
        table_column,
        column_name: str,
        count: int = 1
) -> bool:
    for _ in range(5):
        new_value = await orm.fetchone(
            select(table_column).where(UserCalledCount.group_id == group.id, UserCalledCount.member_id == member.id)
        )
        new_value = new_value[0] + count if new_value else count
        try:
            res = await orm.insert_or_update(
                UserCalledCount,
                [UserCalledCount.group_id == group.id, UserCalledCount.member_id == member.id],
                {"group_id": group.id, "member_id": member.id, column_name: new_value}
            )
            if not res:
                return False
            if column_name != "chat_count":
                await orm.add(
                    FunctionCalledRecord,
                    {
                        "time": datetime.datetime.now(),
                        "group_id": group.id,
                        "member_id": member.id,
                        "function": column_name
                    }
                )
            return True
        except IntegrityError:
            await asyncio.sleep(1)
            continue
        except Exception as e:
            logger.error(e)
            return False


async def get_admins(group: Group) -> list:
    admins_res = list(await orm.fetchall(
        select(
            UserPermission.member_id
        ).where(
            UserPermission.group_id == group.id,
            UserPermission.level > 1
        )
    ))
    return [item[0] for item in admins_res]


async def online_notice(app: Ariadne):
    group_list = await app.getGroupList()
    for group in group_list:
        if await group_setting.get_setting(group.id, Setting.online_notice):
            try:
                await app.sendGroupMessage(group, MessageChain.create([Plain(text="纱雾酱打卡上班啦！")]))
            except AccountMuted:
                pass


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


def get_image_save_number() -> int:
    with open(f"{os.getcwd()}/statics/static_data.json", 'r') as r:
        data = json.loads(r.read())
    data["imageSaveNumber"] += 1
    with open(f"{os.getcwd()}/statics/static_data.json", 'w') as w:
        w.write(json.dumps(data, indent=4))
    return data["imageSaveNumber"]


def load_config(path: str = f"{os.getcwd()}/config.yaml") -> GlobalConfig:
    with open(path, "r", encoding='utf-8') as f:
        configs = yaml.load(f.read(), Loader=yaml.BaseLoader)
        return GlobalConfig(**configs)


async def user_permission_require(group: Union[int, Group], member: Union[int, Member], level: int) -> bool:
    group = group.id if isinstance(group, Group) else group
    member = member.id if isinstance(member, Member) else member
    if result := await orm.fetchone(
        select(
            UserPermission.level
        ).where(
            UserPermission.group_id == group,
            UserPermission.member_id == member
        )
    ):
        return True if result[0] >= level else False
    else:
        try:
            await orm.insert_or_ignore(
                UserPermission,
                [UserPermission.group_id == group, UserPermission.member_id == member],
                {"group_id": group, "member_id": member, "level": 1}
            )
        except:
            pass
        return True if level <= 1 else False


class MessageChainUtils:
    @staticmethod
    async def get_image_content(url: str) -> bytes:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.get(url) as resp:
                return await resp.read()

    @staticmethod
    async def messagechain_to_img(
        message: MessageChain,
        max_width: int = 1080,
        font_size: int = 40,
        spacing: int = 15,
        padding_x: int = 20,
        padding_y: int = 15,
        img_fixed: bool = True,
        font_path: str = f"{os.getcwd()}/statics/fonts/STKAITI.TTF",
    ) -> MessageChain:
        """
        将 MessageChain 转换为图片，仅支持只含有图片/文本的 MessageChain
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
        message = message.merge(copy=True)
        elements = message.__root__

        plains = message.get(Plain)
        text_gather = "\n".join([plain.text for plain in plains])
        # print(max(font.getsize(text)[0] for text in text_gather.split("\n")) + 2 * padding_x)
        final_width = min(max(font.getsize(text)[0] for text in text_gather.split("\n")) + 2 * padding_x, max_width)
        text_width = final_width - 2 * padding_x
        text_height = (font_size + spacing) * (get_final_text_lines(text_gather, text_width, font) + 1)

        img_height_sum = 0
        temp_img_list = []
        images = [element for element in message.__root__ if isinstance(element, Image)]
        for image in images:
            temp_img = IMG.open(BytesIO(await image.get_bytes()))
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
            if isinstance(element, Image):
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
            Image(data_bytes=bytes_io.getvalue())
        ])


class BuildImage:
    """
    快捷生成图片与操作图片的工具类
    """

    def __init__(
        self,
        w: int,
        h: int,
        paste_image_width: int = 0,
        paste_image_height: int = 0,
        color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]] = None,
        image_mode: str = "RGBA",
        font_size: int = 10,
        background: Union[Optional[str], BytesIO, Path] = None,
        font: str = f"{os.getcwd()}/statics/fonts/yz.ttf",
        ratio: float = 1,
        is_alpha: bool = False,
        plain_text: Optional[str] = None,
        font_color: Optional[Union[str, Tuple[int, int, int]]] = None,
    ):
        """
        参数：
            :param w: 自定义图片的宽度，w=0时为图片原本宽度
            :param h: 自定义图片的高度，h=0时为图片原本高度
            :param paste_image_width: 当图片做为背景图时，设置贴图的宽度，用于贴图自动换行
            :param paste_image_height: 当图片做为背景图时，设置贴图的高度，用于贴图自动换行
            :param color: 生成图片的颜色
            :param image_mode: 图片的类型
            :param font_size: 文字大小
            :param background: 打开图片的路径
            :param font: 字体，默认在 resource/ttf/ 路径下
            :param ratio: 倍率压缩
            :param is_alpha: 是否背景透明
            :param plain_text: 纯文字文本
        """
        self.w = int(w)
        self.h = int(h)
        self.paste_image_width = int(paste_image_width)
        self.paste_image_height = int(paste_image_height)
        self.current_w = 0
        self.current_h = 0
        self.font = ImageFont.truetype(font, int(font_size))
        if not plain_text and not color:
            color = (255, 255, 255)
        self.background = background
        if not background:
            if plain_text:
                if not color:
                    color = (255, 255, 255, 0)
                ttf_w, ttf_h = self.getsize(plain_text)
                self.w = self.w if self.w > ttf_w else ttf_w
                self.h = self.h if self.h > ttf_h else ttf_h
            self.markImg = IMG.new(image_mode, (self.w, self.h), color)
            self.markImg.convert(image_mode)
        else:
            if not w and not h:
                self.markImg = IMG.open(background)
                w, h = self.markImg.size
                if ratio and ratio > 0 and ratio != 1:
                    self.w = int(ratio * w)
                    self.h = int(ratio * h)
                    self.markImg = self.markImg.resize(
                        (self.w, self.h), IMG.ANTIALIAS
                    )
                else:
                    self.w = w
                    self.h = h
            else:
                self.markImg = IMG.open(background).resize(
                    (self.w, self.h), IMG.ANTIALIAS
                )
        if is_alpha:
            array = self.markImg.load()
            for i in range(w):
                for j in range(h):
                    pos = array[i, j]
                    is_edit = sum([1 for x in pos[0:3] if x > 240]) == 3
                    if is_edit:
                        array[i, j] = (255, 255, 255, 0)
        self.draw = ImageDraw.Draw(self.markImg)
        self.size = self.w, self.h
        if plain_text:
            fill = font_color if font_color else (0, 0, 0)
            self.text((0, 0), plain_text, fill)
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self.loop = asyncio.get_event_loop()

    async def apaste(
        self,
        img: "BuildImage" or IMG,
        pos: Tuple[int, int] = None,
        alpha: bool = False,
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            异步 贴图
        参数：
            :param img: 已打开的图片文件，可以为 BuildImage 或 Image
            :param pos: 贴图位置（左上角）
            :param alpha: 图片背景是否为透明
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        await self.loop.run_in_executor(None, self.paste, img, pos, alpha, center_type)

    def paste(
        self,
        img: "BuildImage" or IMG,
        pos: Tuple[int, int] = None,
        alpha: bool = False,
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            贴图
        参数：
            :param img: 已打开的图片文件，可以为 BuildImage 或 Image
            :param pos: 贴图位置（左上角）
            :param alpha: 图片背景是否为透明
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        if center_type:
            if center_type not in ["center", "by_height", "by_width"]:
                raise ValueError(
                    "center_type must be 'center', 'by_width' or 'by_height'"
                )
            width, height = 0, 0
            if not pos:
                pos = (0, 0)
            if center_type == "center":
                width = int((self.w - img.w) / 2)
                height = int((self.h - img.h) / 2)
            elif center_type == "by_width":
                width = int((self.w - img.w) / 2)
                height = pos[1]
            elif center_type == "by_height":
                width = pos[0]
                height = int((self.h - img.h) / 2)
            pos = (width, height)
        if isinstance(img, BuildImage):
            img = img.markImg
        if self.current_w == self.w:
            self.current_w = 0
            self.current_h += self.paste_image_height
        if not pos:
            pos = (self.current_w, self.current_h)
        if alpha:
            try:
                self.markImg.paste(img, pos, img)
            except ValueError:
                img = img.convert("RGBA")
                self.markImg.paste(img, pos, img)
        else:
            self.markImg.paste(img, pos)
        self.current_w += self.paste_image_width

    def getsize(self, msg: str) -> Tuple[int, int]:
        """
        说明：
            获取文字在该图片 font_size 下所需要的空间
        参数：
            :param msg: 文字内容
        """
        return self.font.getsize(msg)

    async def apoint(
        self, pos: Tuple[int, int], fill: Optional[Tuple[int, int, int]] = None
    ):
        """
        说明：
            异步 绘制多个或单独的像素
        参数：
            :param pos: 坐标
            :param fill: 填错颜色
        """
        await self.loop.run_in_executor(None, self.point, pos, fill)

    def point(self, pos: Tuple[int, int], fill: Optional[Tuple[int, int, int]] = None):
        """
        说明：
            绘制多个或单独的像素
        参数：
            :param pos: 坐标
            :param fill: 填错颜色
        """
        self.draw.point(pos, fill=fill)

    async def aellipse(
        self,
        pos: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1,
    ):
        """
        说明：
            异步 绘制圆
        参数：
            :param pos: 坐标范围
            :param fill: 填充颜色
            :param outline: 描线颜色
            :param width: 描线宽度
        """
        await self.loop.run_in_executor(None, self.ellipse, pos, fill, outline, width)

    def ellipse(
        self,
        pos: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1,
    ):
        """
        说明：
            绘制圆
        参数：
            :param pos: 坐标范围
            :param fill: 填充颜色
            :param outline: 描线颜色
            :param width: 描线宽度
        """
        self.draw.ellipse(pos, fill, outline, width)

    async def atext(
        self,
        pos: Tuple[int, int],
        text: str,
        fill: Union[str, Tuple[int, int, int]] = (0, 0, 0),
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            异步 在图片上添加文字
        参数：
            :param pos: 文字位置
            :param text: 文字内容
            :param fill: 文字颜色
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        await self.loop.run_in_executor(None, self.text, pos, text, fill, center_type)

    def text(
        self,
        pos: Tuple[int, int],
        text: str,
        fill: Union[str, Tuple[int, int, int]] = (0, 0, 0),
        center_type: Optional[Literal["center", "by_height", "by_width"]] = None,
    ):
        """
        说明：
            在图片上添加文字
        参数：
            :param pos: 文字位置
            :param text: 文字内容
            :param fill: 文字颜色
            :param center_type: 居中类型，可能的值 center: 完全居中，by_width: 水平居中，by_height: 垂直居中
        """
        if center_type:
            if center_type not in ["center", "by_height", "by_width"]:
                raise ValueError(
                    "center_type must be 'center', 'by_width' or 'by_height'"
                )
            w, h = self.w, self.h
            ttf_w, ttf_h = self.getsize(text)
            if center_type == "center":
                w = int((w - ttf_w) / 2)
                h = int((h - ttf_h) / 2)
            elif center_type == "by_width":
                w = int((w - ttf_w) / 2)
                h = pos[1]
            elif center_type == "by_height":
                h = int((h - ttf_h) / 2)
                w = pos[0]
            pos = (w, h)
        self.draw.text(pos, text, fill=fill, font=self.font)

    async def asave(self, path: Optional[Union[str, Path]] = None):
        """
        说明：
            异步 保存图片
        参数：
            :param path: 图片路径
        """
        await self.loop.run_in_executor(None, self.save, path)

    def save(self, path: Optional[Union[str, Path]] = None):
        """
        说明：
            保存图片
        参数：
            :param path: 图片路径
        """
        if not path:
            path = self.background
        self.markImg.save(path)

    def show(self):
        """
        说明：
            显示图片
        """
        self.markImg.show(self.markImg)

    async def aresize(self, ratio: float = 0, w: int = 0, h: int = 0):
        """
        说明：
            异步 压缩图片
        参数：
            :param ratio: 压缩倍率
            :param w: 压缩图片宽度至 w
            :param h: 压缩图片高度至 h
        """
        await self.loop.run_in_executor(None, self.resize, ratio, w, h)

    def resize(self, ratio: float = 0, w: int = 0, h: int = 0):
        """
        说明：
            压缩图片
        参数：
            :param ratio: 压缩倍率
            :param w: 压缩图片宽度至 w
            :param h: 压缩图片高度至 h
        """
        if not w and not h and not ratio:
            raise Exception("缺少参数...")
        if not w and not h and ratio:
            w = int(self.w * ratio)
            h = int(self.h * ratio)
        self.markImg = self.markImg.resize((w, h), IMG.ANTIALIAS)
        self.w, self.h = self.markImg.size
        self.size = self.w, self.h
        self.draw = ImageDraw.Draw(self.markImg)

    async def acrop(self, box: Tuple[int, int, int, int]):
        """
        说明：
            异步 裁剪图片
        参数：
            :param box: 左上角坐标，右下角坐标 (left, upper, right, lower)
        """
        await self.loop.run_in_executor(None, self.crop, box)

    def crop(self, box: Tuple[int, int, int, int]):
        """
        说明：
            裁剪图片
        参数：
            :param box: 左上角坐标，右下角坐标 (left, upper, right, lower)
        """
        self.markImg = self.markImg.crop(box)
        self.w, self.h = self.markImg.size
        self.size = self.w, self.h
        self.draw = ImageDraw.Draw(self.markImg)

    def check_font_size(self, word: str) -> bool:
        """
        说明：
            检查文本所需宽度是否大于图片宽度
        参数：
            :param word: 文本内容
        """
        return self.font.getsize(word)[0] > self.w

    async def atransparent(self, alpha_ratio: float = 1, n: int = 0):
        """
        说明：
            异步 图片透明化
        参数：
            :param alpha_ratio: 透明化程度
            :param n: 透明化大小内边距
        """
        await self.loop.run_in_executor(None, self.transparent, alpha_ratio, n)

    def transparent(self, alpha_ratio: float = 1, n: int = 0):
        """
        说明：
            图片透明化
        参数：
            :param alpha_ratio: 透明化程度
            :param n: 透明化大小内边距
        """
        self.markImg = self.markImg.convert("RGBA")
        x, y = self.markImg.size
        for i in range(n, x - n):
            for k in range(n, y - n):
                color = self.markImg.getpixel((i, k))
                color = color[:-1] + (int(100 * alpha_ratio),)
                self.markImg.putpixel((i, k), color)
        self.draw = ImageDraw.Draw(self.markImg)

    def pic2bs4(self) -> str:
        """
        说明：
            BuildImage 转 base64
        """
        buf = BytesIO()
        self.markImg.save(buf, format="PNG")
        base64_str = base64.b64encode(buf.getvalue()).decode()
        return base64_str

    def pic2bytes(self) -> bytes:
        """
        说明：
            BuildImage 转 base64
        """
        buf = BytesIO()
        self.markImg.save(buf, format="PNG")
        return buf.getvalue()

    def convert(self, type_: str):
        """
        说明：
            修改图片类型
        参数：
            :param type_: 类型
        """
        self.markImg = self.markImg.convert(type_)

    async def arectangle(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: str = None,
        width: int = 1,
    ):
        """
        说明：
            异步 画框
        参数：
            :param xy: 坐标
            :param fill: 填充颜色
            :param outline: 轮廓颜色
            :param width: 线宽
        """
        await self.loop.run_in_executor(None, self.rectangle, xy, fill, outline, width)

    def rectangle(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Tuple[int, int, int]] = None,
        outline: str = None,
        width: int = 1,
    ):
        """
        说明：
            画框
        参数：
            :param xy: 坐标
            :param fill: 填充颜色
            :param outline: 轮廓颜色
            :param width: 线宽
        """
        self.draw.rectangle(xy, fill, outline, width)

    async def apolygon(
        self,
        xy: List[Tuple[int, int]],
        fill: Tuple[int, int, int] = (0, 0, 0),
        outline: int = 1,
    ):
        """
        说明:
            异步 画多边形
        参数：
            :param xy: 坐标
            :param fill: 颜色
            :param outline: 线宽
        """
        await self.loop.run_in_executor(None, self.polygon, xy, fill, outline)

    def polygon(
        self,
        xy: List[Tuple[int, int]],
        fill: Tuple[int, int, int] = (0, 0, 0),
        outline: int = 1,
    ):
        """
        说明:
            画多边形
        参数：
            :param xy: 坐标
            :param fill: 颜色
            :param outline: 线宽
        """
        self.draw.polygon(xy, fill, outline)

    async def aline(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Union[str, Tuple[int, int, int]]] = None,
        width: int = 1,
    ):
        """
        说明：
            异步 画线
        参数：
            :param xy: 坐标
            :param fill: 填充
            :param width: 线宽
        """
        await self.loop.run_in_executor(None, self.line, xy, fill, width)

    def line(
        self,
        xy: Tuple[int, int, int, int],
        fill: Optional[Union[Tuple[int, int, int], str]] = None,
        width: int = 1,
    ):
        """
        说明：
            画线
        参数：
            :param xy: 坐标
            :param fill: 填充
            :param width: 线宽
        """
        self.draw.line(xy, fill, width)

    async def acircle(self):
        """
        说明：
            异步 将 BuildImage 图片变为圆形
        """
        await self.loop.run_in_executor(None, self.circle)

    def circle(self):
        """
        说明：
            将 BuildImage 图片变为圆形
        """
        self.convert("RGBA")
        r2 = min(self.w, self.h)
        if self.w != self.h:
            self.resize(w=r2, h=r2)
        r3 = int(r2 / 2)
        imb = IMG.new("RGBA", (r3 * 2, r3 * 2), (255, 255, 255, 0))
        pim_a = self.markImg.load()  # 像素的访问对象
        pim_b = imb.load()
        r = float(r2 / 2)
        for i in range(r2):
            for j in range(r2):
                lx = abs(i - r)  # 到圆心距离的横坐标
                ly = abs(j - r)  # 到圆心距离的纵坐标
                l_ = (pow(lx, 2) + pow(ly, 2)) ** 0.5  # 三角函数 半径
                if l_ < r3:
                    pim_b[i - (r - r3), j - (r - r3)] = pim_a[i, j]
        self.markImg = imb

    async def acircle_corner(self, radii: int = 30):
        """
        说明：
            异步 矩形四角变圆
        参数：
            :param radii: 半径
        """
        await self.loop.run_in_executor(None, self.circle_corner, radii)

    def circle_corner(self, radii: int = 30):
        """
        说明：
            矩形四角变圆
        参数：
            :param radii: 半径
        """
        # 画圆（用于分离4个角）
        circle = IMG.new("L", (radii * 2, radii * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)
        self.markImg = self.markImg.convert("RGBA")
        w, h = self.markImg.size
        alpha = IMG.new("L", self.markImg.size, 255)
        alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))
        alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))
        alpha.paste(
            circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii)
        )
        alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))
        self.markImg.putalpha(alpha)

    async def arotate(self, angle: int, expand: bool = False):
        """
        说明：
            异步 旋转图片
        参数：
            :param angle: 角度
            :param expand: 放大图片适应角度
        """
        await self.loop.run_in_executor(None, self.rotate, angle, expand)

    def rotate(self, angle: int, expand: bool = False):
        """
        说明：
            旋转图片
        参数：
            :param angle: 角度
            :param expand: 放大图片适应角度
        """
        self.markImg = self.markImg.rotate(angle, expand=expand)

    async def atranspose(self, angle: int):
        """
        说明：
            异步 旋转图片(包括边框)
        参数：
            :param angle: 角度
        """
        await self.loop.run_in_executor(None, self.transpose, angle)

    def transpose(self, angle: int):
        """
        说明：
            旋转图片(包括边框)
        参数：
            :param angle: 角度
        """
        self.markImg.transpose(angle)

    async def afilter(self, filter_: str, aud: int = None):
        """
        说明：
            异步 图片变化
        参数：
            :param filter_: 变化效果
            :param aud: 利率
        """
        await self.loop.run_in_executor(None, self.filter, filter_, aud)

    def filter(self, filter_: str, aud: int = None):
        """
        说明：
            图片变化
        参数：
            :param filter_: 变化效果
            :param aud: 利率
        """
        _x = None
        if filter_ == "GaussianBlur":  # 高斯模糊
            _x = ImageFilter.GaussianBlur
        elif filter_ == "EDGE_ENHANCE":  # 锐化效果
            _x = ImageFilter.EDGE_ENHANCE
        elif filter_ == "BLUR":  # 模糊效果
            _x = ImageFilter.BLUR
        elif filter_ == "CONTOUR":  # 铅笔滤镜
            _x = ImageFilter.CONTOUR
        elif filter_ == "FIND_EDGES":  # 边缘检测
            _x = ImageFilter.FIND_EDGES
        if _x:
            if aud:
                self.markImg = self.markImg.filter(_x(aud))
            else:
                self.markImg = self.markImg.filter(_x)
        self.draw = ImageDraw.Draw(self.markImg)

    async def areplace_color_tran(
        self,
        src_color: Union[
            Tuple[int, int, int], Tuple[Tuple[int, int, int], Tuple[int, int, int]]
        ],
        replace_color: Tuple[int, int, int],
    ):
        """
        说明：
            异步 颜色替换
        参数：
            :param src_color: 目标颜色，或者使用列表，设置阈值
            :param replace_color: 替换颜色
        """
        self.loop.run_in_executor(
            None, self.replace_color_tran, src_color, replace_color
        )

    def replace_color_tran(
        self,
        src_color: Union[
            Tuple[int, int, int], Tuple[Tuple[int, int, int], Tuple[int, int, int]]
        ],
        replace_color: Tuple[int, int, int],
    ):
        """
        说明：
            颜色替换
        参数：
            :param src_color: 目标颜色，或者使用元祖，设置阈值
            :param replace_color: 替换颜色
        """
        if isinstance(src_color, tuple):
            start_ = src_color[0]
            end_ = src_color[1]
        else:
            start_ = src_color
            end_ = None
        for i in range(self.w):
            for j in range(self.h):
                r, g, b = self.markImg.getpixel((i, j))
                if not end_:
                    if r == start_[0] and g == start_[1] and b == start_[2]:
                        self.markImg.putpixel((i, j), replace_color)
                else:
                    if (
                        start_[0] <= r <= end_[0]
                        and start_[1] <= g <= end_[1]
                        and start_[2] <= b <= end_[2]
                    ):
                        self.markImg.putpixel((i, j), replace_color)

    #
    def getchannel(self, type_):
        self.markImg = self.markImg.getchannel(type_)

    def draw_ellipse(self, image, bounds, width=1, outline='white', antialias=4):
        """Improved ellipse drawing function, based on PIL.ImageDraw."""

        # Use a single channel image (mode='L') as mask.
        # The size of the mask can be increased relative to the imput image
        # to get smoother looking results.
        mask = IMG.new(
            size=[int(dim * antialias) for dim in image.size],
            mode='L', color='black')
        draw = ImageDraw.Draw(mask)

        # draw outer shape in white (color) and inner shape in black (transparent)
        for offset, fill in (width / -2.0, 'black'), (width / 2.0, 'white'):
            left, top = [(value + offset) * antialias for value in bounds[:2]]
            right, bottom = [(value - offset) * antialias for value in bounds[2:]]
            draw.ellipse([left, top, right, bottom], fill=fill)

        # downsample the mask using PIL.Image.LANCZOS
        # (a high-quality downsampling filter).
        mask = mask.resize(image.size, IMG.LANCZOS)

        # paste outline color to input image through the mask
        image.putalpha(mask)

    #
    def circle_new(self):
        self.markImg.convert("RGBA")
        size = self.markImg.size
        r2 = min(size[0], size[1])
        if size[0] != size[1]:
            self.markImg = self.markImg.resize((r2, r2), IMG.ANTIALIAS)
        ellipse_box = [0, 0, r2 - 2, r2 - 2]
        self.draw_ellipse(self.markImg, ellipse_box, width=1)


async def get_avatar(qq: Union[int, Member, Friend, Group], size: int = 640) -> Optional[bytes]:
    async with aiohttp.ClientSession() as session:
        if isinstance(qq, Group):
            async with session.get(f"https://p.qlogo.cn/gh/{qq.id}/{qq.id}/{size}/") as resp:
                return await resp.read()
        else:
            if isinstance(qq, Member) or isinstance(qq, Friend):
                qq = qq.id
            async with session.get(f"http://q1.qlogo.cn/g?b=qq&nk={qq}&s={size}") as resp:
                return await resp.read()
