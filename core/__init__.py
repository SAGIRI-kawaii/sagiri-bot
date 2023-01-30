import os
import shutil
import datetime
from abc import ABC
from pathlib import Path
from loguru import logger
from fastapi import FastAPI
from pydantic import BaseModel
from alembic.config import Config
from typing import Dict, List, Type
from alembic.util.exc import CommandError
from alembic.command import revision, upgrade
from fastapi.middleware.cors import CORSMiddleware
from alembic.script.revision import ResolutionError

from graia.saya import Saya
from graia.ariadne import Ariadne
from graia.broadcast import Broadcast
from graia.ariadne.event.message import (
    GroupMessage,
    FriendMessage,
    TempMessage,
    StrangerMessage,
    ActiveMessage,
    ActiveGroupMessage,
    ActiveFriendMessage,
)
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config,
)
from graiax.playwright import PlaywrightService
from graia.ariadne.model import LogConfig, Group
from creart import create, add_creator, exists_module
from graia.amnesia.builtins.uvicorn import UvicornService
from graiax.fastapi import FastAPIBehaviour, FastAPIService
from graia.saya.builtins.broadcast import BroadcastBehaviour
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.orm import orm
from shared.utils.string import set_log
from shared.models.config import GlobalConfig
from shared.models.blacklist import GroupBlackList
from shared.models.public_group import PublicGroup
from shared.models.types import ModuleOperationType
from shared.utils.self_upgrade import UpdaterService
from shared.models.group_setting import GroupSetting
from shared.models.permission import GroupPermission
from shared.orm.tables import Setting, UserPermission

non_log = {
    GroupMessage,
    FriendMessage,
    TempMessage,
    StrangerMessage,
    ActiveMessage,
    ActiveGroupMessage,
    ActiveFriendMessage
}


class Sagiri(object):
    apps: List[Ariadne]
    config: GlobalConfig
    base_path: str | Path
    launch_time: datetime.datetime
    sent_count: int = 0
    received_count: int = 0
    initialized: bool = False

    def __init__(self, g_config: GlobalConfig, base_path: str | Path):
        self.launch_time = datetime.datetime.now()
        self.config = create(GlobalConfig)
        self.base_path = base_path if isinstance(base_path, Path) else Path(base_path)
        self.apps = [Ariadne(
            config(
                bot_account,
                str(g_config.verify_key),
                HttpClientConfig(host=g_config.mirai_host),
                WebsocketClientConfig(host=g_config.mirai_host),
            ),
            log_config=LogConfig(lambda x: None if type(x) in non_log else "INFO"),
        ) for bot_account in self.config.bot_accounts]
        # logger.disable("uvicorn")
        if self.config.default_account:
            Ariadne.config(default_account=self.config.default_account)
        Ariadne.launch_manager.add_service(
            PlaywrightService(
                "chromium",
                proxy={"server": self.config.proxy} if self.config.proxy != "proxy" else None
            )
        )
        Ariadne.launch_manager.add_service(UpdaterService())

        # 推后导入，避免循环导入
        from shared.utils.alembic import AlembicService

        Ariadne.launch_manager.add_service(AlembicService())
        if self.config.web_manager_api:
            Ariadne.launch_manager.add_service(
                UvicornService(
                    host="0.0.0.0" if self.config.api_expose else "127.0.0.1",
                    port=self.config.api_port
                )
            )
            fastapi = FastAPI()
            fastapi.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            create(Saya).install_behaviours(FastAPIBehaviour(fastapi))
            Ariadne.launch_manager.add_service(FastAPIService(fastapi))
        self.config_check()

    async def initialize(self):
        if self.initialized:
            return
        self.initialized = True
        self.set_logger()
        logger.info("Sagiri Initializing...")
        bcc = create(Broadcast)
        saya = create(Saya)
        saya.install_behaviours(BroadcastBehaviour(bcc))
        await orm.update(Setting, [], {"active": False})
        total_groups = {}
        for app in self.apps:
            group_list = await app.get_group_list()
            for group in group_list:
                await orm.insert_or_update(
                    Setting,
                    [Setting.group_id == group.id],
                    {"group_id": group.id, "group_name": group.name, "active": True},
                )
            await self.update_host_permission(group_list)
            total_groups[app.account] = group_list
        logger.info("本次启动活动群组如下：")
        for account, group_list in total_groups.items():
            for group in group_list:
                logger.info(f"Bot账号: {str(account).ljust(14)}群ID: {str(group.id).ljust(14)}群名: {group.name}")
        await create(GroupSetting).data_init()
        await create(GroupBlackList).data_init()
        await create(GroupPermission).data_init()

    @staticmethod
    async def public_group_init(app: Ariadne):
        await create(PublicGroup).add_account(app=app)

    async def update_host_permission(self, group_list: List[Group]):
        for group in group_list:
            await orm.insert_or_update(
                UserPermission,
                [
                    UserPermission.member_id == self.config.host_qq,
                    UserPermission.group_id == group.id,
                ],
                {"member_id": self.config.host_qq, "group_id": group.id, "level": 4},
            )

    def set_logger(self):
        logger.add(
            Path.cwd() / "log" / "{time:YYYY-MM-DD}" / "common.log",
            level="INFO",
            retention=f"{self.config.log_related['common_retention']} days",
            encoding="utf-8",
            rotation=datetime.time(),
        )
        logger.add(
            Path.cwd() / "log" / "{time:YYYY-MM-DD}" / "error.log",
            level="ERROR",
            retention=f"{self.config.log_related['error_retention']} days",
            encoding="utf-8",
            rotation=datetime.time(),
        )
        logger.add(set_log)

    async def set_group_account(self):
        pass

    def config_check(self) -> None:
        """配置检查"""
        required_key = ("bot_accounts", "default_account", "host_qq", "mirai_host", "verify_key")
        logger.info("Start checking configuration\n-----------------------------------------------")
        father_properties = tuple(dir(BaseModel))
        properties = [
            _
            for _ in dir(self.config)
            if _ not in father_properties and not _.startswith("_")
        ]
        for key in properties:
            value = self.config.__getattribute__(key)
            if key in required_key and key == value:
                logger.error(f"Required initial value not changed detected: {key} - {value}")
                exit(0)
            elif isinstance(value, dict):
                logger.success(f"{key}:")
                self.dict_check(value)
            elif key == value:
                logger.warning(f"Unchanged initial value detected: {key} - {value}")
            else:
                logger.success(f"{key} - {value}")
        logger.info("Configuration check completed\n-----------------------------------------------")

    @staticmethod
    def dict_check(dictionary: dict, indent: int = 4) -> None:
        for key in dictionary:
            if isinstance(dictionary[key], dict):
                logger.success(f"{' ' * indent}{key}:")
                Sagiri.dict_check(dictionary[key], indent + 4)
            elif dictionary[key] == key:
                logger.warning(f"{' ' * indent}Unchanged initial value detected: {key} - {dictionary[key]}")
            else:
                logger.success(f"{' ' * indent}{key} - {dictionary[key]}")

    @staticmethod
    def install_modules(base_path: str | Path, recursion_install: bool = False) -> Dict[str, Exception]:
        """加载 base_path 中的模块

        Args:
            base_path(str | Path): 要进行加载的文件夹路径，只支持bot文件夹下的文件夹，使用相对路径（从main.py所在文件夹开始）, 如 Path("module") / "saya"
            recursion_install(bool): 是否加载 base_path 内的所有 installable 的模块（包括所有单文件模块、包模块以及base_path下属所有文件夹内的单文件模块、包模块）

        Returns:
            一个包含模块路径和加载时产生的错误的字典, example: {"module.test", ImportError}

        """
        if isinstance(base_path, str):
            base_path = Path(base_path)
        saya = create(Saya)
        module_base_path = base_path.as_posix().replace("/", ".")
        exceptions = {}
        ignore = {"__pycache__", "__init__.py"}
        with saya.module_context():
            for module in os.listdir(str(base_path)):
                if module in ignore:
                    continue
                try:
                    if (base_path / module).is_dir():
                        if (base_path / module / "__init__.py").exists():
                            saya.require(f"{module_base_path}.{module}")
                        elif recursion_install:
                            Sagiri.install_modules(base_path / module, recursion_install)
                    elif (base_path / module).is_file():
                        saya.require(f"{module_base_path}.{module.split('.')[0]}")
                except Exception as e:
                    logger.exception("")
                    exceptions[str(base_path / module.split('.')[0])] = e
        return exceptions

    @staticmethod
    def module_operation(modules: str | list[str], operation_type: ModuleOperationType) -> dict[str, Exception]:
        saya = create(Saya)
        exceptions = {}
        if isinstance(modules, str):
            modules = [modules]
        if operation_type == ModuleOperationType.INSTALL:
            op_modules = {
                module: module
                for module in modules
            }
        else:
            loaded_channels = saya.channels
            op_modules = {
                module: loaded_channels[module]
                for module in modules
                if module in loaded_channels
            }
        with saya.module_context():
            for c, value in op_modules.items():
                try:
                    if operation_type == ModuleOperationType.INSTALL:
                        saya.require(c)
                    elif operation_type == ModuleOperationType.UNINSTALL:
                        saya.uninstall_channel(value)
                    else:
                        saya.reload_channel(value)
                except Exception as e:
                    exceptions[c] = e
        return exceptions

    async def alembic(self):
        if not (Path.cwd() / "alembic").exists():
            logger.info("未检测到alembic目录，进行初始化")
            os.system("alembic init alembic")
            with open(Path.cwd() / "resources" / "alembic_env_py_content.txt", "r") as r:
                alembic_env_py_content = r.read()
            with open(Path.cwd() / "alembic" / "env.py", "w") as w:
                w.write(alembic_env_py_content)
            db_link = self.config.db_link
            db_link = db_link.split(":")[0].split("+")[0] + ":" + ":".join(db_link.split(":")[1:])
            logger.warning(f"尝试自动更改 sqlalchemy.url 为 {db_link}，若出现报错请自行修改")
            alembic_ini_path = Path.cwd() / "alembic.ini"
            lines = alembic_ini_path.read_text(encoding="utf-8").split("\n")
            for i, line in enumerate(lines):
                if line.startswith("sqlalchemy.url"):
                    lines[i] = line.replace("driver://user:pass@localhost/dbname", db_link)
                    break
            alembic_ini_path.write_text("\n".join(lines))
        alembic_version_path = Path.cwd() / "alembic" / "versions"
        if not alembic_version_path.exists():
            alembic_version_path.mkdir()
        cfg = Config(file_="alembic.ini", ini_section="alembic")
        try:
            revision(cfg, message="update", autogenerate=True)
            upgrade(cfg, "head")
        except (CommandError, ResolutionError):
            _ = await orm.reset_version()
            shutil.rmtree(alembic_version_path)
            alembic_version_path.mkdir()
            revision(cfg, message="update", autogenerate=True)
            upgrade(cfg, "head")

        # os.system("alembic revision --autogenerate -m 'update'")
        # os.system("alembic upgrade head")

    @staticmethod
    def launch():
        Ariadne.launch_blocking()

    async def restart(self):
        ...


class SagiriClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("core", "Sagiri"),)

    @staticmethod
    def available() -> bool:
        return exists_module("core")

    @staticmethod
    def create(create_type: Type[Sagiri]) -> Sagiri:
        return Sagiri(create(GlobalConfig), Path.cwd())


add_creator(SagiriClassCreator)
