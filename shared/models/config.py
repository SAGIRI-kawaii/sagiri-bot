import yaml
import json
from abc import ABC
from pathlib import Path
from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import Type, List, Dict, Any

from creart import create, add_creator, exists_module
from creart.creator import AbstractCreator, CreateTargetInfo


class PluginMeta(BaseModel):
    name: str = ""
    version: str = "0.1"
    display_name: str = ""
    authors: List[str] = []
    description: str = ""
    usage: List[str] = []
    example: List[str] = []
    maintaining: bool = False
    icon: str = ""
    prefix: List[str] = []
    triggers: List[str] = []
    metadata: Dict[str, Any] = {}


def load_plugin_meta(path: Path | str) -> PluginMeta:
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


def get_plugin_config(module: str) -> PluginConfig:
    config: GlobalConfig = create(GlobalConfig)
    commands = config.commands
    return commands.get(module, commands.get("default")).copy()


class GlobalConfig(BaseModel):
    bot_accounts: List[int]
    default_account: int | None
    host_qq: int
    mirai_host: str = "http://localhost:8080"
    verify_key: str = "1234567890"
    db_link: str = "sqlite+aiosqlite:///data.db"
    api_port: int = 54321
    api_expose: bool = False
    web_manager_api: bool = False
    web_manager_auto_boot: bool = False
    gallery: dict = {}
    proxy: str = "proxy"
    auto_upgrade: bool = False
    commands: Dict[str, PluginConfig]
    functions: dict = {
        "tencent": {"secret_id": "secret_id", "secret_key": "secret_key"},
        "saucenao_api_key": "saucenao_api_key",
        "lolicon_api_key": "lolicon_api_key",
        "wolfram_alpha_key": "wolfram_alpha_key",
        "github": {"username": "username", "token": "token"},
        "stable_diffusion_api": "stable_diffusion_api",
        "lolicon": {}
    }
    log_related: dict = {"error_retention": 14, "common_retention": 7}

    def get_proxy(self) -> str:
        return self.proxy if self.proxy != "proxy" else ""


class ConfigClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.models.config", "GlobalConfig"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.models.config")

    @staticmethod
    def create(create_type: Type[GlobalConfig]) -> GlobalConfig:
        with open(Path().cwd() / "config" / "config.yaml", "r", encoding="utf-8") as f:
            configs = yaml.safe_load(f.read())
            config = GlobalConfig(**configs)
            if not config.default_account:
                config.default_account = config.bot_accounts[0]
            return config


add_creator(ConfigClassCreator)
