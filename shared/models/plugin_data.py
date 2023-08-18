from typing import Literal
from dataclasses import field, dataclass

import kayaku
from kayaku import config
from avilla.core import Selector, Message

from shared.utils.models import selector2pattern

DEFAULT_NOTICE = True
DEFAULT_SWITCH = True
DEFAULT_GLOBAL_SWITCH = True
SceneType = Message | Selector | str


@dataclass
class Setting:
    notice: bool
    switch: bool
    
    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise AttributeError

    def __setitem__(self, key, value):
        if hasattr(self, key):
            return setattr(self, key, value)
        raise AttributeError

    def __delitem__(self, key):
        if hasattr(self, key):
            del self.data[key]
        else:
            raise AttributeError


@config("system.plugin_data")
class PluginData:
    switch: dict[str, dict[str, Setting]] = field(default_factory=dict)
    global_switch: dict[str, bool] = field(default_factory=dict)
    scenes: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    """
    switch: {
        module_name: {
            scene1: Setting,
            scenc2: Setting
        }
    }
    global_switch: {
        module_name1: True,
        module_name2: False
    }
    """
    
    @staticmethod
    def parse_scene(scene: SceneType) -> str:
        if isinstance(scene, Message):
            scene = scene.scene
        if not isinstance(scene, str):
            scene = selector2pattern(scene)
        return scene
    
    def add_scene(self, scene: SceneType):
        scene = self.parse_scene(scene)
        if scene not in self.scenes:
            self.scenes.append(scene)
            for module in self.switch:
                if scene not in self.switch[module]:
                    self.switch[module][scene] = {
                        "switch": DEFAULT_SWITCH,
                        "notice": DEFAULT_NOTICE
                    }
        kayaku.save(self.__class__)
    
    def remove_scene(self, scene: SceneType):
        scene = self.parse_scene(scene)
        if scene in self.scenes:
            self.scenes = [s for s in self.scenes if s != scene]
            for module in self.switch:
                if scene in self.switch[module]:
                    del self.switch[module][scene]
        kayaku.save(self.__class__)

    def add_plugin(self, plugin: str, switch: bool = DEFAULT_SWITCH, notice: bool = DEFAULT_NOTICE):
        if plugin not in self.plugins:
            self.plugins.append(plugin)
        if plugin not in self.switch:
            self.switch[plugin] = {scene: {"switch": switch, "notice": notice} for scene in self.scenes}
        if plugin not in self.global_switch:
            self.global_switch[plugin] = DEFAULT_GLOBAL_SWITCH
        kayaku.save(self.__class__)
    
    def remove_plugin(self, plugin: str):
        if plugin in self.plugins:
            self.scenes = [p for p in self.plugins if p != plugin]
        if plugin in self.switch:
            del self.switch[plugin]
        if plugin in self.global_switch:
            del self.global_switch[plugin]
    
    def is_on(self, plugin: str, scene: SceneType) -> bool:
        scene = self.parse_scene(scene)
        self.add_plugin(plugin)
        self.add_scene(scene)
        return self.switch[plugin][scene]["switch"]
    
    def is_notice_on(self, plugin: str, scene: SceneType) -> bool:
        scene = self.parse_scene(scene)
        self.add_plugin(plugin)
        self.add_scene(scene)
        return self.switch[plugin][scene]["notice"]

    def value_change(self, plugin: str, scene: SceneType, key: Literal["switch", "notice"], value: bool):
        self.add_plugin(plugin)
        self.add_scene(scene)
        self.switch[plugin][scene][key] = value

    def switch_on(self, plugin: str, scene: SceneType):
        self.value_change(plugin, scene, "switch", True)

    def switch_off(self, plugin: str, scene: SceneType):
        self.value_change(plugin, scene, "switch", False)
    
    def notice_on(self, plugin: str, scene: SceneType):
        self.value_change(plugin, scene, "notice", True)
    
    def notice_off(self, plugin: str, scene: SceneType):
        self.value_change(plugin, scene, "notice", False)
