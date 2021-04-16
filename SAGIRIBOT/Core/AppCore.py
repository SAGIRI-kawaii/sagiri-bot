import os
import asyncio
import traceback
import threading
from loguru import logger
from asyncio.events import AbstractEventLoop

from graia.saya import Saya
from sqlalchemy import select
from graia.application import Session
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast import BroadcastBehaviour

from .Exceptions import *
from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.ORM.Tables import Setting, UserPermission
from SAGIRIBOT.frequency_limit_module import GlobalFrequencyLimitDict
from SAGIRIBOT.exception_resender import ExceptionReSender, exception_resender_listener


class AppCore:
    __instance = None
    __first_init: bool = False
    __app: GraiaMiraiApplication = None
    __loop: AbstractEventLoop = None
    __bcc = None
    __saya = None
    __thread_pool = None
    __config: dict = None
    __launched: bool = False
    __group_handler_chain = []
    __exception_resender: ExceptionReSender = None
    __frequency_limit_instance: GlobalFrequencyLimitDict = None
    necessary_parameters = ["miraiHost", "authKey", "BotQQ"]

    def __new__(cls, config: dict):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, config: dict):
        if not self.__first_init:
            logger.info("Initializing")
            if any(parameter not in config for parameter in self.necessary_parameters):
                raise ValueError(f"Missing necessary parameters! (miraiHost, authKey, BotQQ)")
            self.__loop = asyncio.get_event_loop()
            self.__bcc = Broadcast(loop=self.__loop)
            self.__app = GraiaMiraiApplication(
                broadcast=self.__bcc,
                connect_info=Session(
                    host=config["miraiHost"],
                    authKey=config["authKey"],
                    account=config["BotQQ"],
                    websocket=True
                ),
                enable_chat_log=False
            )
            self.__saya = Saya(self.__bcc)
            self.__saya.install_behaviours(BroadcastBehaviour(self.__bcc))
            self.__app.debug = False
            self.__config = config
            AppCore.__first_init = True
            logger.info("Initialize end")
        else:
            raise AppCoreAlreadyInitialized()

    @classmethod
    def get_core_instance(cls):
        if cls.__instance:
            return cls.__instance
        else:
            raise AppCoreNotInitialized()

    def get_bcc(self) -> Broadcast:
        if self.__bcc:
            return self.__bcc
        else:
            raise AppCoreNotInitialized()

    def get_loop(self) -> AbstractEventLoop:
        if self.__loop:
            return self.__loop
        else:
            raise AppCoreNotInitialized()

    def get_app(self) -> GraiaMiraiApplication:
        if self.__app:
            return self.__app
        else:
            raise AppCoreNotInitialized()

    def get_config(self):
        return self.__config

    def launch(self):
        if not self.__launched:
            self.__app.launch_blocking()
            self.__launched = True
        else:
            raise GraiaMiraiApplicationAlreadyLaunched()

    def set_group_chain(self, chain: list):
        self.__group_handler_chain = chain

    def get_group_chain(self):
        return self.__group_handler_chain

    def get_frequency_limit_instance(self):
        return self.__frequency_limit_instance

    def get_exception_resender(self):
        return self.__exception_resender

    async def bot_launch_init(self):
        self.config_check()
        orm.session.query(Setting).update({"active": False})
        group_list = await self.__app.groupList()
        frequency_limit_dict = {}
        for group in group_list:
            frequency_limit_dict[group.id] = 0
            try:
                orm.update(Setting, {"group_id": group.id}, {"group_id": group.id, "group_name": group.name, "active": True})
            except Exception:
                logger.error(traceback.format_exc())
                orm.session.rollback()
        results = orm.fetchall(select(Setting).where(Setting.active == True))
        logger.info("本次启动活动群组如下：")
        for result in results:
            logger.info(f"群ID: {str(result[0]).ljust(14)}群名: {result[1]}")
        for result in results:
            orm.update(
                UserPermission,
                {"member_id": self.__config["HostQQ"], "group_id": result[0]},
                {"member_id": self.__config["HostQQ"], "group_id": result[0], "level": 4}
            )
        self.__frequency_limit_instance = GlobalFrequencyLimitDict(frequency_limit_dict)
        exception_resender_instance = ExceptionReSender(self.__app)
        listener = threading.Thread(
            target=exception_resender_listener,
            args=(self.__app, exception_resender_instance, self.__loop)
        )
        listener.start()

    def config_check(self):
        logger.info("checking config")
        pic_paths = ["setuPath", "setu18Path", "realPath", "realHighqPath", "wallpaperPath", "sketchPath"]
        if self.__config["HostQQ"] == 123:
            logger.warning(f"HostQQ无效，请检查配置！")
        for path in pic_paths:
            if not os.path.exists(self.__config[path]):
                logger.warning(f"{path}无效，请检查配置！")
        if self.__config["saucenaoCookie"] == "balabala":
            logger.warning("saucenaoCookie无效，请检查配置！")
        if self.__config["txAppId"] == "1234567890":
            logger.warning("txAppId无效，请检查配置！")
        if self.__config["txAppKey"] == "ABCDEFGHIJKLMN":
            logger.warning("txAppKey无效，请检查配置！")
        logger.info("check done")

    def load_saya_modules(self):
        ignore = ["__init__.py", "__pycache__"]
        with self.__saya.module_context():
            for module in os.listdir(f"modules"):
                if module in ignore:
                    continue
                try:
                    if os.path.isdir(module):
                        self.__saya.require(f"modules.{module}")
                    else:
                        self.__saya.require(f"modules.{module.split('.')[0]}")
                except ModuleNotFoundError as e:
                    logger.error(f"saya模块：{module} - {e}")

    def get_saya_channels(self):
        return self.__saya.channels
