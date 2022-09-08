import json
import contextlib
from abc import ABC
from pathlib import Path
from typing import Dict, NoReturn, Type
from json.decoder import JSONDecodeError

from graia.ariadne.event.message import Group
from creart import add_creator, exists_module, create
from creart.creator import AbstractCreator, CreateTargetInfo

DEFAULT_SWITCH = True
DEFAULT_NOTICE = False

saya_data_instance = None


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

    def add_group(self, group: Group | int | str) -> NoReturn:
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

    def remove_group(self, group: Group | int | str) -> NoReturn:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
        if group in self.permission:
            del self.permission[group]
        for key in self.switch:
            if group in self.switch[key]:
                del self.switch[key][group]
        self.save()

    def add_saya(self, name: str, switch: bool = DEFAULT_SWITCH, notice: bool = DEFAULT_NOTICE) -> None:
        if name not in self.switch:
            self.switch[name] = {group: {"switch": switch, "notice": notice} for group in self.permission}
        self.save()

    def remove_saya(self, name: str) -> None:
        if name in self.switch:
            del self.switch[name]
        self.save()

    def is_turned_on(self, name: str, group: Group | int | str) -> bool:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
        if self.switch.get(name):
            if "0" in self.switch[name] and self.switch[name]["0"] is False:
                return False
            if group in self.switch[name]:
                return self.switch[name][group]["switch"]
            self.add_group(group)
        else:
            self.add_saya(name)
            if not self.switch[name].get(group):
                self.add_group(group)
        return DEFAULT_SWITCH

    def is_notice_on(self, name: str, group: Group | int | str) -> bool:
        if isinstance(group, Group):
            group = group.id
        group = str(group)
        if self.switch.get(name):
            if group in self.switch[name]:
                return self.switch[name][group]["notice"]
            self.add_group(group)
        else:
            self.add_saya(name)
            if not self.switch[name].get(group):
                self.add_group(group)
        return DEFAULT_NOTICE

    def value_change(
        self, name: str, group: Group | int | str, key: str, value: bool
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

    def switch_on(self, name: str, group: Group | int | str) -> None:
        self.value_change(name, group, "switch", True)

    def switch_off(self, name: str, group: Group | int | str) -> None:
        self.value_change(name, group, "switch", False)

    def notice_on(self, name: str, group: Group | int | str) -> None:
        self.value_change(name, group, "notice", True)

    def notice_off(self, name: str, group: Group | int | str) -> None:
        self.value_change(name, group, "notice", False)

    def save(self, path: str = str(Path(__file__).parent.joinpath("saya_data.json"))):
        with open(path, "w") as w:
            w.write(
                json.dumps(
                    {"switch": self.switch, "permission": self.permission}, indent=4
                )
            )

    def load(self, path: str = str(Path(__file__).parent.joinpath("saya_data.json"))) -> "SayaData":
        with contextlib.suppress(FileNotFoundError, JSONDecodeError):
            with open(path, "r") as r:
                data = json.load(r)
                self.switch = data.get("switch", {})
                self.permission = data.get("permission", {})
        return self


def get_saya_data():
    global saya_data_instance
    if not saya_data_instance:
        saya_data_instance = create(SayaData)
    return saya_data_instance


class SayaDataClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.models.saya_data", "SayaData"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.models.saya_data")

    @staticmethod
    def create(create_type: Type[SayaData]) -> SayaData:
        return SayaData().load()


add_creator(SayaDataClassCreator)
