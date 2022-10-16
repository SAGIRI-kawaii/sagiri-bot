from pathlib import Path

from creart import create
from graia.saya import Saya
from graia.ariadne.model.relationship import Group

from core import Sagiri
from shared.models.saya_data import SayaData

saya = create(Saya)
core = create(Sagiri)


def saya_is_turned_on(name: str, group: int | Group):
    saya_data = create(SayaData)
    group = group.id if isinstance(group, Group) else group
    group = str(group)
    if name not in saya_data.switch:
        print(name, "not found!")
        saya_data.add_saya(name)
    if group not in saya_data.switch[name]:
        saya_data.add_group(group)
    return saya_data.is_turned_on(name, group)


def get_all_channels() -> list[str]:
    ignore = ["__init__.py", "__pycache__"]
    dirs = [
        "modules/required",
        "modules/self_contained",
        "modules/third_party"
    ]
    modules = []
    for path in dirs:
        for module in Path(path).glob("*"):
            module = module.as_posix()
            if str(module).split("/")[-1] in ignore:
                continue
            if (core.base_path / module).is_dir():
                modules.append(str(module).replace("/", "."))
            else:
                modules.append(str(module).split(".")[0].replace("/", "."))
    return modules


def get_installed_channels() -> list[str]:
    return list(saya.channels.keys())


def get_not_installed_channels() -> list[str]:
    return [c for c in get_all_channels() if c not in saya.channels]
