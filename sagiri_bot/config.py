import os
import yaml
import json
from abc import ABC
from pathlib import Path
from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import Type, List, Dict, Union, Any

from creart import add_creator
from creart import exists_module
from creart.creator import AbstractCreator, CreateTargetInfo


class PluginMeta(BaseModel):
    name: str = ""
    version: str = "0.1"
    display_name: str = ""
    authors: List[str] = []
    description: str = ""
    usage: str = ""
    example: str = ""
    icon: str = ""
    prefix: List[str] = []
    triggers: List[str] = []
    metadata: Dict[str, Any] = {}


def load_plugin_meta(path: Union[Path, str]) -> PluginMeta:
    if isinstance(path, str):
        path = Path(path)
    if path.is_file():
        path = path.parent
    if (path / "metadata.json").exists():
        with open(path / "metadata.json", "r", encoding="utf-8") as r:
            data = json.load(r)
            return PluginMeta(**data)
    return PluginMeta()


def load_plugin_meta_by_module(module: str) -> PluginMeta:
    paths = module.split('.')
    base_path = Path().cwd()
    for path in paths:
        base_path = base_path / path
    return load_plugin_meta(base_path)


class PluginConfig(TypedDict):
    prefix: List[str]
    alias: List[str]


class GlobalConfig(BaseModel):
    bot_qq: int
    host_qq: int
    mirai_host: str = "http://localhost:8080"
    verify_key: str = "1234567890"
    db_link: str = "sqlite+aiosqlite:///data.db"
    web_manager_api: bool = False
    web_manager_auto_boot: bool = False
    image_path: dict = {}
    proxy: str = "proxy"
    commands: Dict[str, PluginConfig]
    functions: dict = {
        "tencent": {"secret_id": "secret_id", "secret_key": "secret_key"},
        "saucenao_api_key": "saucenao_api_key",
        "lolicon_api_key": "lolicon_api_key",
        "wolfram_alpha_key": "wolfram_alpha_key",
        "github": {"username": "username", "token": "token"},
    }
    log_related: dict = {"error_retention": 14, "common_retention": 7}
    data_related: dict = {
        "lolicon_image_cache": True,
        "network_data_cache": False,
        "automatic_update": False,
        "data_retention": False,
    }


class ConfigClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("sagiri_bot.config", "GlobalConfig"),)

    @staticmethod
    def available() -> bool:
        return exists_module("sagiri_bot.config")

    @staticmethod
    def create(create_type: Type[GlobalConfig]) -> GlobalConfig:
        with open(Path(os.getcwd()) / "config.yaml", "r", encoding="utf-8") as f:
            configs = yaml.safe_load(f.read())
            return GlobalConfig(**configs)


add_creator(ConfigClassCreator)
