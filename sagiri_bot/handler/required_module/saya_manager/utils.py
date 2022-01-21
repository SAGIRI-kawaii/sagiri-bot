import os
import json
from loguru import logger
from typing import Dict, Union

from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.ariadne.message.chain import MessageChain, Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.core.app_core import AppCore


DEFAULT_SWITCH = True
DEFAULT_NOTICE = False


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton


def manageable(name: str) -> Depend:
    async def manage(app: Ariadne, group: Group):
        if name not in saya_data.switch:
            saya_data.add_saya(name)
        if group.id not in saya_data.switch[name]:
            saya_data.add_group(group)
        if not saya_data.is_turned_on(name, group):
            if saya_data.is_notice_on(name, group):
                await app.sendMessage(group, MessageChain.create([Plain(text=f"{name}插件已关闭，请联系管理员")]))
            raise ExecutionStop()
    return Depend(manage)


def saya_init():
    channels = Saya.current().channels
    core = AppCore.get_core_instance()
    bcc = core.get_bcc()
    for channel in channels.values():
        cubes = channel.content
        logger.info(f"installing saya module: {channel._name}")
        for cube in cubes:
            if isinstance(cube.metaclass, ListenerSchema):
                bcc.removeListener(bcc.getListener(cube.content))
                cube.metaclass.decorators.append(manageable(channel.module))
                listener = cube.metaclass.build_listener(cube.content, bcc)
                if not listener.namespace:
                    listener.namespace = bcc.getDefaultNamespace()
                bcc.listeners.append(listener)
                if not cube.metaclass.inline_dispatchers:
                    logger.warning(f"插件{channel._name}未使用inline_dispatchers！默认notice为False！")
                    saya_data.add_saya(channel.module, notice=False)
                else:
                    saya_data.add_saya(channel.module)


@singleton
class SayaData:
    permission: Dict[int, Dict[int, int]]
    switch: Dict[str, Dict[int, Dict[str, bool]]]
    """
    permission = {
        group: {
            member: level(int)
        }
    }
    switch = {
        channel_module: {
            group: {
                notice: bool,
                switch: bool
            }
        },
        ...
    }
    """
    def __init__(
            self,
            permission: Dict[int, Dict[int, int]] = None,
            switch: Dict[str, Dict[int, Dict[str, bool]]] = None
    ):
        self.permission = permission if permission else {}
        self.switch = switch if switch else {}

    def add_group(self, group: Union[Group, int]) -> None:
        if isinstance(group, Group):
            group = group.id
        if group not in self.permission:
            self.permission[group] = {}
        for key in self.switch:
            if group not in self.switch[key]:
                self.switch[key][group] = {}
                self.switch[key][group]["switch"] = DEFAULT_SWITCH
                self.switch[key][group]["notice"] = DEFAULT_NOTICE
        self.save()

    def remove_group(self, group: Union[Group, int]) -> None:
        if isinstance(group, Group):
            group = group.id
        if group in self.permission:
            del self.permission[group]
        for key in self.switch:
            if group in self.switch[key]:
                del self.switch[key][group]
        self.save()

    def add_saya(self, name: str, switch: bool = DEFAULT_SWITCH, notice: bool = DEFAULT_NOTICE) -> None:
        if name not in self.switch:
            self.switch[name] = {}
            for group in self.permission:
                self.switch[name][group] = {}
                self.switch[name][group]["switch"] = switch
                self.switch[name][group]["notice"] = notice
        self.save()

    def remove_saya(self, name: str) -> None:
        if name in self.switch:
            del self.switch[name]
        self.save()

    def is_turned_on(self, name: str, group: Union[Group, int]) -> bool:
        if isinstance(group, Group):
            group = group.id
        if self.switch.get(name):
            if group in self.switch[name]:
                return self.switch[name][group]["switch"]
            else:
                self.add_group(group)
                return DEFAULT_SWITCH
        else:
            self.add_saya(name)
            if not self.switch[name].get(group):
                self.add_group(group)
            return DEFAULT_SWITCH

    def is_notice_on(self, name: str, group: Union[Group, int]) -> bool:
        if isinstance(group, Group):
            group = group.id
        if self.switch.get(name):
            if group in self.switch[name]:
                return self.switch[name][group]["notice"]
            else:
                self.add_group(group)
                return DEFAULT_NOTICE
        else:
            self.add_saya(name)
            if not self.switch[name].get(group):
                self.add_group(group)
            return DEFAULT_NOTICE

    def value_change(self, name: str, group: Union[Group, int], key: str, value: bool) -> None:
        if isinstance(group, Group):
            group = group.id
        if self.switch.get(name):
            if group not in self.switch[name]:
                self.add_group(group)
        else:
            self.add_saya(name)
            if not self.switch[name].get(group):
                self.add_group(group)
        self.switch[name][group][key] = value
        self.save()

    def switch_on(self, name: str, group: Union[Group, int]) -> None:
        self.value_change(name, group, "switch", True)

    def switch_off(self, name: str, group: Union[Group, int]) -> None:
        self.value_change(name, group, "switch", False)

    def notice_on(self, name: str, group: Union[Group, int]) -> None:
        self.value_change(name, group, "notice", True)

    def notice_off(self, name: str, group: Union[Group, int]) -> None:
        self.value_change(name, group, "notice", False)

    def save(self, path: str = f"{os.getcwd()}/saya_data.json"):
        with open(path, "w") as w:
            w.write(json.dumps({"switch": self.switch, "permission": self.permission}, indent=4))

    def load(self, path: str = f"{os.getcwd()}/saya_data.json") -> "SayaData":
        try:
            with open(path, "r") as r:
                data = json.load(r)
                self.switch = data.get("switch", {})
                self.permission = data.get("permission", {})
        except FileNotFoundError:
            pass
        return self


saya_data = SayaData().load()
