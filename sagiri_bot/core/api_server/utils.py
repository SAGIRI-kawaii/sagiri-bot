import os
import json
import hashlib
from json import JSONDecodeError
from typing import Union, Optional, List, Dict

from graia.saya import Channel
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image

from .models import User
from sagiri_bot.core.app_core import AppCore


def md5(content: str) -> str:
    return hashlib.md5(content.encode(encoding='utf-8')).hexdigest()


def get_all_channels() -> List[str]:
    ignore = ["__init__.py", "__pycache__"]
    dirs = ["modules", "sagiri_bot/handler/required_module", "sagiri_bot/handler/handlers"]
    modules = []
    for path in dirs:
        for module in os.listdir(path):
            if module in ignore:
                continue
            if os.path.isdir(module):
                modules.append(f"{path.replace('/', '.')}.{module}")
            else:
                modules.append(f"{path.replace('/', '.')}.{module.split('.')[0]}")
    return modules


def get_not_installed_channels() -> List[str]:
    installed_channels = AppCore.get_core_instance().get_saya().channels.keys()
    all_channels = get_all_channels()
    return [channel for channel in all_channels if channel not in installed_channels]


def get_installed_channels() -> Dict[str, Channel]:
    return AppCore.get_core_instance().get_saya().channels


def load_channel(modules: Union[str, List[str]]) -> Dict[str, Exception]:
    ignore = ["__init__.py", "__pycache__"]
    exceptions = {}
    if isinstance(modules, str):
        modules = [modules]
    with AppCore.get_core_instance().get_saya().module_context():
        for module in modules:
            if module in ignore:
                continue
            try:
                AppCore.get_core_instance().get_saya().require(module)
            except Exception as e:
                exceptions[module] = e
    return exceptions


def parse_messagechain(message: list) -> Union[MessageChain, list]:
    """
    {
        type: str(Union[plain, image]),
        data: {
            content: Optional[Union[str, bytes]],
            url: Optional[str],
            path: Optional[str]
        }
    }
    """
    elements = []
    exceptions = []
    for element in message:
        if element["type"] == "plain":
            if content := element.get("content"):
                elements.append(Plain(content))
            else:
                exceptions.append((element, "missing parameter: content"))
        elif element["type"] == "image":
            if content := element.get("content"):
                elements.append(Image(data_bytes=content))
            elif url := element.get("url"):
                elements.append(Image(url=url))
            elif path := element.get("path"):
                elements.append(Image(path=path))
            else:
                exceptions.append((element, "missing parameter: content(bytes) / url(str) / path(str)"))
    return MessageChain(elements) if not exceptions else exceptions


class UserData:
    _instance = None
    _data = {}
    _path: str = f"{os.path.dirname(__file__)}/data.json"

    def __new__(cls, path: str = f"{os.path.dirname(__file__)}/data.json"):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, path: str = f"{os.path.dirname(__file__)}/data.json"):
        if not os.path.exists(path):
            os.mknod(path)
        with open(path, "r") as r:
            try:
                self._data = json.load(r)
                self._path = path
            except JSONDecodeError:
                self.user_data = {}

    def add_user(self, user: User) -> None:
        self._data[user.user_name] = md5(user.password)
        self.save()

    def has_user(self, user: Union[str, User]) -> bool:
        if isinstance(user, User):
            user = user.user_name
        return user in self._data.keys()

    def get_user(self, user_name: str) -> Optional[User]:
        if user_name in self._data.keys():
            return User(user_name=user_name, password=self._data[user_name])
        return None

    def save(self) -> None:
        with open(self._path, "w") as w:
            w.write(json.dumps(self._data, indent=4))


user_data = UserData()
