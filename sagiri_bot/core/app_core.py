import os
import time
from loguru import logger
from pydantic import BaseModel
from asyncio.events import AbstractEventLoop
from sqlalchemy.exc import InternalError, ProgrammingError

from creart import create
from graia.saya import Saya
from graia.broadcast import Broadcast
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config,
)
from graia.ariadne.event.message import (
    GroupMessage,
    FriendMessage,
    TempMessage,
    StrangerMessage,
    ActiveMessage,
    ActiveGroupMessage,
    ActiveFriendMessage,
)
from graia.ariadne.model import LogConfig
from graia.saya.builtins.broadcast import BroadcastBehaviour

try:
    from graia.scheduler import GraiaScheduler
    from graia.scheduler.saya import GraiaSchedulerBehaviour

    _install_scheduler = True
except (ModuleNotFoundError, ImportError):
    _install_scheduler = False

from .exceptions import *
from sagiri_bot.orm.async_orm import orm
from sagiri_bot.internal_utils import group_setting
from sagiri_bot.config import GlobalConfig
from sagiri_bot.orm.async_orm import Setting, UserPermission

non_log = {
    GroupMessage,
    FriendMessage,
    TempMessage,
    StrangerMessage,
    ActiveMessage,
    ActiveGroupMessage,
    ActiveFriendMessage,
}


class AppCore(object):
    """
    应用核心，用于管理所有相关组件
    """

    __instance = None
    __first_init: bool = False
    __app: Ariadne = None
    __config: GlobalConfig = None
    start_time = time.time()
    necessary_parameters = ["miraiHost", "verify_key", "BotQQ"]

    def __new__(cls, g_config: GlobalConfig):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, g_config: GlobalConfig):
        if self.__first_init:
            raise AppCoreAlreadyInitialized()
        logger.info("Initializing")
        loop = create(AbstractEventLoop)
        bcc = create(Broadcast)
        self.__app = Ariadne(
            config(
                g_config.bot_qq,
                str(g_config.verify_key),
                HttpClientConfig(host=g_config.mirai_host),
                WebsocketClientConfig(host=g_config.mirai_host),
            ),
            log_config=LogConfig(lambda x: None if type(x) in non_log else "INFO"),
        )
        saya = create(Saya)
        saya.install_behaviours(BroadcastBehaviour(bcc))
        if _install_scheduler:
            self.__sche = GraiaScheduler(loop=loop, broadcast=bcc)
            saya.install_behaviours(GraiaSchedulerBehaviour(self.__sche))
        self.__app.debug = False
        self.__config = g_config
        AppCore.__first_init = True
        logger.info("Initialize end")

    def get_app(self) -> Ariadne:
        return self.__app

    def launch(self) -> None:
        """启动 Ariadne 实例"""
        try:
            self.__app.launch_blocking()
        except KeyboardInterrupt:
            print("stop")
            self.__app.stop()

    @logger.catch
    async def bot_launch_init(self) -> None:
        """机器人启动初始化"""
        self.config_check()
        try:
            await orm.init_check()
        except (AttributeError, InternalError, ProgrammingError):
            await orm.create_all()
        if not os.path.exists(f"{os.getcwd()}/alembic"):
            logger.info("未检测到alembic目录，进行初始化")
            os.system("alembic init alembic")
            with open(f"{os.getcwd()}/statics/alembic_env_py_content.txt", "r") as r:
                alembic_env_py_content = r.read()
            with open(f"{os.getcwd()}/alembic/env.py", "w") as w:
                w.write(alembic_env_py_content)
            logger.warning(
                f"请前往更改 {os.getcwd()}/alembic.ini 文件，将其中的 sqlalchemy.url 替换为自己的数据库url（不需注明引擎）后重启机器人"
            )
            exit()
        if not os.path.exists(f"{os.getcwd()}/alembic/versions"):
            os.mkdir(f"{os.getcwd()}/alembic/versions")
        os.system("alembic revision --autogenerate -m 'update'")
        os.system("alembic upgrade head")
        await orm.update(Setting, [], {"active": False})
        group_list = await self.__app.get_group_list()
        frequency_limit_dict = {}
        for group in group_list:
            frequency_limit_dict[group.id] = 0
            await orm.insert_or_update(
                Setting,
                [Setting.group_id == group.id],
                {"group_id": group.id, "group_name": group.name, "active": True},
            )
        self.load_required_saya_modules()
        logger.info("本次启动活动群组如下：")
        for group in group_list:
            logger.info(f"群ID: {str(group.id).ljust(14)}群名: {group.name}")
            await orm.insert_or_update(
                UserPermission,
                [
                    UserPermission.member_id == self.__config.host_qq,
                    UserPermission.group_id == group.id,
                ],
                {"member_id": self.__config.host_qq, "group_id": group.id, "level": 4},
            )
        await group_setting.data_init()

    @staticmethod
    def dict_check(dictionary: dict, indent: int = 4) -> None:
        for key in dictionary:
            if isinstance(dictionary[key], dict):
                logger.success(f"{' ' * indent}{key}:")
                AppCore.dict_check(dictionary[key], indent + 4)
            elif dictionary[key] == key:
                logger.warning(
                    f"{' ' * indent}Unchanged initial value detected: {key} - {dictionary[key]}"
                )
            else:
                logger.success(f"{' ' * indent}{key} - {dictionary[key]}")

    def config_check(self) -> None:
        """配置检查"""
        required_key = ("bot_qq", "host_qq", "mirai_host", "verify_key")
        logger.info("Start checking configuration")
        father_properties = tuple(dir(BaseModel))
        properties = [
            _
            for _ in dir(self.__config)
            if _ not in father_properties and not _.startswith("_")
        ]
        for key in properties:
            value = self.__config.__getattribute__(key)
            if key in required_key and key == value:
                logger.error(
                    f"Required initial value not changed detected: {key} - {value}"
                )
                exit(0)
            elif isinstance(value, dict):
                logger.success(f"{key}:")
                self.dict_check(value)
            elif key == value:
                logger.warning(f"Unchanged initial value detected: {key} - {value}")
            else:
                logger.success(f"{key} - {value}")
        logger.info("Configuration check completed")

    @staticmethod
    def load_saya_modules() -> None:
        """加载自定义 saya 模块"""
        ignore = ["__init__.py", "__pycache__"]
        saya = create(Saya)
        with saya.module_context():
            for module in os.listdir("modules"):
                if module in ignore:
                    continue
                try:
                    if os.path.isdir(module):
                        saya.require(f"modules.{module}")
                    else:
                        saya.require(f"modules.{module.split('.')[0]}")
                except ModuleNotFoundError as e:
                    logger.error(f"saya模块：{module} - {e}")

    @staticmethod
    def load_required_saya_modules() -> None:
        """加载必要 saya 模块"""
        ignore = ["__init__.py", "__pycache__"]
        saya = create(Saya)
        with saya.module_context():
            for module in os.listdir("sagiri_bot/handler/required_module"):
                if module in ignore:
                    continue
                try:
                    if os.path.isdir(module):
                        saya.require(
                            f"sagiri_bot.handler.required_module.{module}"
                        )
                    else:
                        saya.require(
                            f"sagiri_bot.handler.required_module.{module.split('.')[0]}"
                        )
                except ModuleNotFoundError as e:
                    logger.error(f"saya模块：{module} - {e}")
                except Exception as e:
                    logger.error(f"saya模块：{module} - {e}")

    def load_schedulers(self):
        pass
