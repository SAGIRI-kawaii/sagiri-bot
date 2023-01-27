import re
import os
import json
import time
import random
import aiohttp
from abc import ABC
from pathlib import Path
from loguru import logger
from aiohttp import TCPConnector
from typing import Type, Literal
from dataclasses import dataclass

from graia.ariadne.message.element import Image
from graia.ariadne.event.message import Group, Member
from creart import create, add_creator, exists_module
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.utils.control import Permission
from shared.models.config import GlobalConfig

gallerys = create(GlobalConfig).gallery.keys()
json_pattern = r"json:([\w\W]+\.)+([\w\W]+)\$"
url_pattern = r"((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"


async def valid2send(
        group: Group, member: Member, gallery_name: str
) -> bool | Literal["PermissionError", "IntervalError", "GalleryClosed"]:
    interval = create(GalleryInterval)
    g_data = create(GalleryConfig).get_config(gallery_name)
    if interval.valid2send(group, gallery_name):
        if (await Permission.get(group, member)) >= g_data.privilege:
            if create(GallerySwitch).is_open(group, gallery_name):
                return True
            interval.renew_time(group, gallery_name)
            return "GalleryClosed"
        return "PermissionError"
    return "IntervalError"


def random_pic(base_path: Path | str) -> str:
    if isinstance(base_path, str):
        base_path = Path(base_path)
    path_dir = os.listdir(base_path)
    path = random.sample(path_dir, 1)[0]
    return str(base_path / path)


async def get_image(gallery_name: str) -> Image | str:
    config = create(GalleryConfig).get_config(gallery_name)
    path = config.path
    proxy = create(GlobalConfig).proxy
    proxy = (proxy if proxy != "proxy" else "") if config.need_proxy else ""
    if re.match(json_pattern + url_pattern, path):
        json_paths = path.split("$")[0].split(":")[1].split(".")
        url = path.split("$")[1]
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(url, proxy=proxy) as resp:
                res = await resp.json(content_type=resp.content_type)
            for jp in json_paths:
                try:
                    res = res[int(jp[1:])] if jp[0] == "|" and jp[1:].isnumeric() else res.get(jp)
                except TypeError:
                    logger.error("json解析失败！")
                    return "json解析失败！请查看配置路径是否正确或API是否有变动！"
            async with session.get(res, proxy=proxy) as resp:
                return Image(data_bytes=await resp.read())
    elif re.match(url_pattern, path):
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(path, proxy=proxy) as resp:
                return Image(data_bytes=await resp.read())
    elif Path(path).exists():
        return Image(path=random_pic(path))
    return Image(path=Path.cwd() / "resources" / "error" / "path_not_exists.png")


async def save_image_to_gallery(path: str | Path, images: list[Image]) -> dict[str, Exception]:
    path = Path(path)
    exceptions = {}
    for image in images:
        try:
            img_content = await image.get_bytes()
            print(image.id)
            image_id, suffix = str(image.id).split(".")
            img_path = Path(f"{image_id[1:-1]}.{suffix}")
            img_path.with_stem(img_path.stem[1:-1])
            if img_path.suffix == ".mirai":
                img_path = img_path.with_suffix(".jpg")
            save_path = path / img_path
            save_path.write_bytes(img_content)
            logger.success(f"成功保存图片：{save_path}")
        except Exception as e:
            exceptions[image.id] = e
    return exceptions


@dataclass
class GalleryData(object):
    path: str
    privilege: int = 1
    interval: float = 0
    need_proxy: bool = False
    default_switch: bool = True


class GalleryConfig(object):
    configs: dict[str, GalleryData]

    def __init__(self):
        config = create(GlobalConfig).gallery
        self.configs = {}
        for name, data in config.items():
            try:
                self.configs[name] = GalleryData(**data)
            except Exception as e:
                logger.error(f"图库{name}配置读取发生错误{e}")

    def get_config(self, gallery_name: str) -> GalleryData | None:
        return self.configs.get(gallery_name)


class GalleryConfigCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("modules.self_contained.gallery.utils", "GalleryConfig"),)

    @staticmethod
    def available() -> bool:
        return exists_module("modules.self_contained.gallery.utils")

    @staticmethod
    def create(create_type: Type[GalleryConfig]) -> GalleryConfig:
        return GalleryConfig()


class GalleryInterval(object):
    last_send: dict[int, dict[str, float]]

    def __init__(self, groups: list[Group] | None = None):
        self.last_send = {group.id: {gallery: 0 for gallery in gallerys} for group in groups} if groups else {}

    def valid2send(self, group: Group, gallery_name: str) -> bool:
        if group.id in self.last_send:
            if gallery_name in self.last_send[group.id]:
                if g_data := create(GalleryConfig).get_config(gallery_name):
                    return time.time() - self.last_send[group.id][gallery_name] > g_data.interval
            self.last_send[group.id][gallery_name] = 0
            return True
        self.last_send[group.id] = {gallery: 0 for gallery in gallerys}
        return True

    def renew_time(self, group: Group, gallery_name: str, t: float | None = None):
        self.last_send[group.id][gallery_name] = t or time.time()


class GalleryIntervalCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("modules.self_contained.gallery.utils", "GalleryInterval"),)

    @staticmethod
    def available() -> bool:
        return exists_module("modules.self_contained.gallery.utils")

    @staticmethod
    def create(create_type: Type[GalleryInterval]) -> GalleryInterval:
        return GalleryInterval()


class GallerySwitch(object):
    switch: dict[str, dict[str, bool]]

    def __init__(self):
        self.load()

    def add_group(self, group: Group | int | str):
        group = str(group.id if isinstance(group, Group) else group)
        if group not in self.switch:
            g_config = create(GalleryConfig)
            self.switch[group] = {g_name: g_data.default_switch for g_name, g_data in g_config.configs.items()}

    def add_gallery(self, gallery_name: str):
        g_config = create(GalleryConfig)
        for group, dic in self.switch.items():
            if gallery_name not in dic:
                if g_data := g_config.get_config(gallery_name):
                    self.switch[group][gallery_name] = g_data.default_switch

    def load(self):
        file_path = Path(__file__).parent / "gallery_switch.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as r:
                self.switch = json.load(r)
        else:
            self.switch = {}

    def save(self):
        file_path = Path(__file__).parent / "gallery_switch.json"
        with open(file_path, "w", encoding="utf-8") as w:
            w.write(json.dumps(self.switch, indent=4, ensure_ascii=False))

    def is_open(self, group: Group | int | str, gallery_name: str) -> bool:
        group = str(group.id if isinstance(group, Group) else group)
        if group not in self.switch:
            self.add_group(group)
        if gallery_name not in self.switch[group]:
            self.add_gallery(gallery_name)
        return self.switch[group][gallery_name]

    def modify(self, group: Group | int | str, gallery_name: str, new_value: bool):
        group = str(group.id if isinstance(group, Group) else group)
        if group not in self.switch:
            self.add_group(group)
        if gallery_name not in self.switch[group]:
            self.add_gallery(gallery_name)
        self.switch[group][gallery_name] = new_value
        self.save()


class GallerySwitchCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("modules.self_contained.gallery.utils", "GallerySwitch"),)

    @staticmethod
    def available() -> bool:
        return exists_module("modules.self_contained.gallery.utils")

    @staticmethod
    def create(create_type: Type[GallerySwitch]) -> GallerySwitch:
        return GallerySwitch()


add_creator(GalleryConfigCreator)
add_creator(GalleryIntervalCreator)
add_creator(GallerySwitchCreator)
