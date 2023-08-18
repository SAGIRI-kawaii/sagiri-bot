import time
from abc import ABC
from typing import Mapping, Type
from sqlalchemy.types import String
from sqlalchemy.orm import Mapped, mapped_column
from dataclasses import dataclass, field, asdict

import kayaku
from avilla.core import Selector
from kayaku import config, create
from creart import add_creator, exists_module
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.database.model import Base
from shared.utils.models import selector2pattern

SceneType = Selector | Mapping[str, str]


@dataclass
class Gallery:
    path: str = ""
    privilege: int = field(default=1)
    interval: int = field(default=0)
    default_switch: bool = field(default=True)
    need_proxy: bool = field(default=False)
    cache: bool = field(default=False)
    cache_path: str = ""


@config("modules.gallery")
class GalleryConfig:
    configs: dict[str, Gallery] = field(default_factory=lambda: {"name": asdict(Gallery())})
    command_separator: str = "#"

    def __getitem__(self, key: str) -> Gallery | None:
        for k in self.configs:
            if str(k) == key:
                return self.configs[k]
        return None


class GalleryTriggerWord(Base):
    __tablename__ = "gallery_trigger_word"

    keyword: Mapped[str] = mapped_column(String(), nullable=False, primary_key=True, unique=True)
    gallery: Mapped[str] = mapped_column(String(), nullable=False)


class GalleryInterval:
    last_send: dict[int, dict[str, float]]

    def __init__(self, scenes: list[str | SceneType] | None = None):
        gallerys = create(GalleryConfig)
        self.last_send = {
            selector2pattern(scene) if not isinstance(scene, str) else scene: 
            {str(gallery): 0 for gallery in gallerys.configs.keys()} for scene in scenes
        } if scenes else {}

    def valid2send(self, scene: str | SceneType, gallery_name: str) -> bool:
        if not isinstance(scene, str):
            scene = selector2pattern(scene)
        if scene in self.last_send:
            if gallery_name in self.last_send[scene]:
                if g_data := create(GalleryConfig)[gallery_name]:
                    if g_data.interval > 0:
                        return time.time() - self.last_send[scene][gallery_name] > g_data.interval
            self.last_send[scene][gallery_name] = 0
            return True
        self.last_send[scene] = {str(gallery): 0 for gallery in create(GalleryConfig).configs.keys()}
        return True

    def renew_time(self, scene: str | SceneType, gallery_name: str, t: float | None = None):
        if not isinstance(scene, str):
            scene = selector2pattern(scene)
        self.last_send[scene][gallery_name] = t or time.time()


class GalleryIntervalCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("modules.common.gallery.models", "GalleryInterval"),)

    @staticmethod
    def available() -> bool:
        return exists_module("modules.common.gallery.models")

    @staticmethod
    def create(create_type: Type[GalleryInterval]) -> GalleryInterval:
        return GalleryInterval()
    

@config("modules.control.gallery_switch")
class GallerySwitch:
    switch: dict[str, dict[str, bool]] = field(default_factory=dict)

    def add_scene(self, scene: SceneType | str):
        if not isinstance(scene, str):
            scene = selector2pattern(scene)
        if scene not in self.switch:
            g_config = create(GalleryConfig)
            self.switch[scene] = {g_name: g_data.default_switch for g_name, g_data in g_config.configs.items()}
        kayaku.save(self.__class__)

    def add_gallery(self, gallery_name: str):
        g_config = create(GalleryConfig)
        for group, dic in self.switch.items():
            if gallery_name not in dic:
                if g_data := g_config[gallery_name]:
                    self.switch[group][gallery_name] = g_data.default_switch
        kayaku.save(self.__class__)

    def is_on(self, scene: SceneType | str, gallery_name: str) -> bool:
        if not isinstance(scene, str):
            scene = selector2pattern(scene)
        if scene not in self.switch:
            self.add_scene(scene)
        if gallery_name not in self.switch[scene]:
            self.add_gallery(gallery_name)
        kayaku.save(self.__class__)
        return self.switch[scene][gallery_name]

    def modify(self, scene: SceneType | str, gallery_name: str, new_value: bool):
        if not isinstance(scene, str):
            scene = selector2pattern(scene)
        if scene not in self.switch:
            self.add_scene(scene)
        if gallery_name not in self.switch[scene]:
            self.add_gallery(gallery_name)
        self.switch[scene][gallery_name] = new_value
        kayaku.save(self.__class__)


add_creator(GalleryIntervalCreator)
