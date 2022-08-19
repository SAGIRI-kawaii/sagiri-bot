import json
from pathlib import Path
from loguru import logger
from typing import Dict, Union
from json.decoder import JSONDecodeError

from creart import create
from graia.saya import Saya
from graia.broadcast import Broadcast
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.ariadne.message.chain import MessageChain, Plain
from graia.ariadne.event.mirai import MiraiEvent, GroupEvent
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.config import load_plugin_meta_by_module

DEFAULT_SWITCH = True
DEFAULT_NOTICE = False


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton


def manageable(name: str, group_events: bool = True) -> Depend:
    async def manage_group_events(app: Ariadne, group: Group):
        if name not in saya_data.switch:
            saya_data.add_saya(name)
        if group.id not in saya_data.switch[name]:
            saya_data.add_group(group)
        if not saya_data.is_turned_on(name, group):
            if saya_data.is_notice_on(name, group):
                await app.send_message(
                    group, MessageChain([Plain(text=f"{name}插件已关闭，请联系管理员")])
                )
            raise ExecutionStop()

    async def manage_mirai_events(app: Ariadne, event: MiraiEvent):
        group = event.group_id if hasattr(event, "group_id") else "0"
        if name not in saya_data.switch:
            saya_data.add_saya(name)
        if group not in saya_data.switch[name]:
            saya_data.add_group(group)
        if not saya_data.is_turned_on(name, group):
            if saya_data.is_notice_on(name, group):
                if group != "0":
                    await app.send_group_message(
                        int(group), MessageChain([Plain(text=f"{name}插件已关闭，请联系管理员")])
                    )
            raise ExecutionStop()

    return Depend(manage_group_events) if group_events else Depend(manage_mirai_events)


def saya_init():
    channels = Saya.current().channels
    bcc = create(Broadcast)
    for channel in channels.values():
        cubes = channel.content
        logger.info(f"converting saya module: {channel.module}")
        for cube in cubes:
            if isinstance(cube.metaclass, ListenerSchema):
                bcc.removeListener(bcc.getListener(cube.content))
                if all(
                    issubclass(i, GroupEvent)
                    for i in cube.metaclass.listening_events
                ):
                    cube.metaclass.decorators.append(manageable(channel.module))
                else:
                    cube.metaclass.decorators.append(manageable(channel.module, False))
                listener = cube.metaclass.build_listener(cube.content, bcc)
                if not listener.namespace:
                    listener.namespace = bcc.getDefaultNamespace()
                bcc.listeners.append(listener)
                if not cube.metaclass.inline_dispatchers:
                    logger.warning(
                        f"插件{channel._name}未使用inline_dispatchers！默认notice为False！"
                    )
                    saya_data.add_saya(channel.module, notice=False)
                else:
                    saya_data.add_saya(channel.module)


@singleton
class SayaData:
    permission: Dict[str, Dict[int, int]]
    switch: Dict[str, Dict[str, Dict[str, bool]]]
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
        permission: Dict[str, Dict[int, int]] = None,
        switch: Dict[str, Dict[str, Dict[str, bool]]] = None,
    ):
        self.permission = permission or {}
        self.switch = switch or {}

    def add_group(self, group: Union[Group, int, str]) -> None:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
        if group not in self.permission:
            self.permission[group] = {}
        for key in self.switch:
            if group not in self.switch[key]:
                self.switch[key][group] = {
                    "switch": DEFAULT_SWITCH,
                    "notice": DEFAULT_NOTICE,
                }
        self.save()

    def remove_group(self, group: Union[Group, int, str]) -> None:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
        if group in self.permission:
            del self.permission[group]
        for key in self.switch:
            if group in self.switch[key]:
                del self.switch[key][group]
        self.save()

    def add_saya(
        self, name: str, switch: bool = DEFAULT_SWITCH, notice: bool = DEFAULT_NOTICE
    ) -> None:
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

    def is_turned_on(self, name: str, group: Union[Group, int, str]) -> bool:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
        if self.switch.get(name):
            if "0" in self.switch[name] and self.switch[name]["0"] is False:
                return False
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

    def is_notice_on(self, name: str, group: Union[Group, int, str]) -> bool:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
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

    def value_change(
        self, name: str, group: Union[Group, int, str], key: str, value: bool
    ) -> None:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
        if self.switch.get(name):
            if group not in self.switch[name]:
                self.add_group(group)
        else:
            self.add_saya(name)
            if not self.switch[name].get(group):
                self.add_group(group)
        self.switch[name][group][key] = value
        self.save()

    def switch_on(self, name: str, group: Union[Group, int, str]) -> None:
        self.value_change(name, group, "switch", True)

    def switch_off(self, name: str, group: Union[Group, int, str]) -> None:
        self.value_change(name, group, "switch", False)

    def notice_on(self, name: str, group: Union[Group, int, str]) -> None:
        self.value_change(name, group, "notice", True)

    def notice_off(self, name: str, group: Union[Group, int, str]) -> None:
        self.value_change(name, group, "notice", False)

    def save(self, path: str = str(Path(__file__).parent.joinpath("saya_data.json"))):
        with open(path, "w") as w:
            w.write(
                json.dumps(
                    {"switch": self.switch, "permission": self.permission}, indent=4
                )
            )

    def load(
        self, path: str = str(Path(__file__).parent.joinpath("saya_data.json"))
    ) -> "SayaData":
        try:
            with open(path, "r") as r:
                data = json.load(r)
                self.switch = data.get("switch", {})
                self.permission = data.get("permission", {})
        except (FileNotFoundError, JSONDecodeError):
            pass
        return self


def reloadable(module: str) -> bool:
    plugin_meta = load_plugin_meta_by_module(module)
    return plugin_meta.metadata.get("reloadable", True)


def uninstallable(module: str) -> bool:
    plugin_meta = load_plugin_meta_by_module(module)
    return plugin_meta.metadata.get("uninstallable", True)


saya_data = SayaData().load()
