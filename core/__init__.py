import os
import datetime

from abc import ABC
from pathlib import Path
from loguru import logger
from pydantic import BaseModel
from typing import Dict, List, Type
from sqlalchemy.exc import InternalError, ProgrammingError

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
from graia.saya.builtins.broadcast import BroadcastBehaviour
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.models.config import GlobalConfig
from shared.utils.self_upgrade import self_upgrade
from shared.models.blacklist import GroupBlackList
from shared.orm import orm, Setting, UserPermission
from shared.models.group_setting import GroupSetting

non_log = {
    GroupMessage,
    FriendMessage,
    TempMessage,
    StrangerMessage,
    ActiveMessage,
    ActiveGroupMessage,
    ActiveFriendMessage,
}


class Sagiri(object):
    app: Ariadne
    config: GlobalConfig
    main_path: str | Path
    launch_time: datetime.datetime

    def __init__(self, g_config: GlobalConfig, main_path: str | Path):
        self.launch_time = datetime.datetime.now()
        self.config = create(GlobalConfig)
        self.main_path = main_path if isinstance(main_path, Path) else Path(main_path)
        self.app = Ariadne(
            config(
                g_config.bot_qq,
                str(g_config.verify_key),
                HttpClientConfig(host=g_config.mirai_host),
                WebsocketClientConfig(host=g_config.mirai_host),
            ),
            log_config=LogConfig(lambda x: None if type(x) in non_log else "INFO"),
        )
        self.app.launch_manager.add_service(
            PlaywrightService(
                "chromium",
                proxy={"server": self.config.proxy if self.config.proxy != "proxy" else None}
            )
        )

    async def initialize(self):
        self.set_logger()
        logger.info("Sagiri Initializing...")
        bcc = create(Broadcast)
        saya = create(Saya)
        saya.install_behaviours(BroadcastBehaviour(bcc))
        self.app.debug = False
        self.config_check()
        try:
            await orm.init_check()
        except (AttributeError, InternalError, ProgrammingError):
            await orm.create_all()
        self.alembic()
        await orm.update(Setting, [], {"active": False})
        group_list = await self.app.get_group_list()
        for group in group_list:
            await orm.insert_or_update(
                Setting,
                [Setting.group_id == group.id],
                {"group_id": group.id, "group_name": group.name, "active": True},
            )
        _ = await self.update_host_permission(group_list)
        _ = await self_upgrade()
        logger.info("本次启动活动群组如下：")
        for group in group_list:
            logger.info(f"群ID: {str(group.id).ljust(14)}群名: {group.name}")
        await create(GroupSetting).data_init()
        await create(GroupBlackList).data_init()

    async def update_host_permission(self, group_list: List[Group] | None = None):
        if not group_list:
            group_list = await self.app.get_group_list()
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

    def config_check(self) -> None:
        """配置检查"""
        required_key = ("bot_qq", "host_qq", "mirai_host", "verify_key")
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
    def alembic():
        if not (Path.cwd() / "alembic").exists():
            logger.info("未检测到alembic目录，进行初始化")
            os.system("alembic init alembic")
            with open(Path.cwd() / "resources" / "alembic_env_py_content.txt", "r") as r:
                alembic_env_py_content = r.read()
            with open(Path.cwd() / "alembic" / "env.py", "w") as w:
                w.write(alembic_env_py_content)
            logger.warning(
                f"请前往更改 {Path.cwd() / 'alembic.ini'} 文件，"
                "将其中的 sqlalchemy.url 替换为自己的数据库url（不需注明引擎）后重启机器人"
            )
            exit()
        if not (Path.cwd() / "alembic" / "versions").exists():
            (Path.cwd() / "alembic" / "versions").mkdir()
        os.system("alembic revision --autogenerate -m 'update'")
        os.system("alembic upgrade head")

    def launch(self):
        self.app.launch_blocking()

    async def restart(self): ...


class SagiriClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("core", "Sagiri"),)

    @staticmethod
    def available() -> bool:
        return exists_module("core")

    @staticmethod
    def create(create_type: Type[Sagiri]) -> Sagiri:
        return Sagiri(create(GlobalConfig), Path.cwd())


add_creator(SagiriClassCreator)