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
from SAGIRIBOT.ORM.AsyncORM import orm
from SAGIRIBOT.ORM.AsyncORM import Setting, UserPermission
from SAGIRIBOT.frequency_limit_module import GlobalFrequencyLimitDict, frequency_limit
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
    __group_handler_chain = {}
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

    def set_group_chain(self, chains: list):
        for chain in chains:
            self.__group_handler_chain[chain.__name__] = chain

    def get_group_chains(self):
        return self.__group_handler_chain

    def get_group_chain(self, chain_name: str):
        return self.__group_handler_chain[chain_name] if chain_name in self.__group_handler_chain else None

    def get_frequency_limit_instance(self):
        return self.__frequency_limit_instance

    def get_exception_resender(self):
        return self.__exception_resender

    async def bot_launch_init(self):
        self.config_check()
        try:
            await orm.create_all()
            if not os.path.exists(f"{os.getcwd()}/alembic"):
                logger.info("未检测到alembic目录，进行初始化")
                os.system("alembic init alembic")
                from SAGIRIBOT.static_datas import alembic_env_py_content
                with open(f"{os.getcwd()}/alembic/env.py", "w") as w:
                    w.write(alembic_env_py_content)
                logger.warning(f"请前往更改 {os.getcwd()}/alembic.ini 文件，将其中的 sqlalchemy.url 替换为自己的数据库url（不需注明引擎）\n")
                while input(f"完成请输入是：") != "是":
                    pass
            if not os.path.exists(f"{os.getcwd()}/alembic/versions"):
                os.mkdir(f"{os.getcwd()}/alembic/versions")
            os.system("alembic revision --autogenerate -m 'update'")
            os.system("alembic upgrade head")
            await orm.update(Setting, [], {"active": False})
            group_list = await self.__app.groupList()
            frequency_limit_dict = {}
            for group in group_list:
                frequency_limit_dict[group.id] = 0
                await orm.insert_or_update(
                    Setting,
                    [Setting.group_id == group.id],
                    {"group_id": group.id, "group_name": group.name, "active": True}
                )
            results = await orm.fetchall(select(Setting.group_id, Setting.group_name).where(Setting.active == True))
            logger.info("本次启动活动群组如下：")
            for result in results:
                logger.info(f"群ID: {str(result.group_id).ljust(14)}群名: {result.group_name}")
            for result in results:
                await orm.insert_or_update(
                    UserPermission,
                    [UserPermission.member_id == self.__config["HostQQ"], UserPermission.group_id == result[0]],
                    {"member_id": self.__config["HostQQ"], "group_id": result[0], "level": 4}
                )
            self.__frequency_limit_instance = GlobalFrequencyLimitDict(frequency_limit_dict)
            threading.Thread(target=frequency_limit, args=(self.__frequency_limit_instance,)).start()
            exception_resender_instance = ExceptionReSender(self.__app)
            listener = threading.Thread(
                target=exception_resender_listener,
                args=(self.__app, exception_resender_instance, self.__loop)
            )
            listener.start()
        except:
            logger.error(traceback.format_exc())
            exit()

    def config_check(self):
        logger.info("checking config")
        pic_paths = ["setuPath", "setu18Path", "realPath", "realHighqPath", "wallpaperPath", "sketchPath"]
        if self.__config["HostQQ"] == 123:
            logger.warning(f"HostQQ无效，请检查配置！")
        for path in pic_paths:
            if not os.path.exists(self.__config[path]):
                logger.warning(f"{path}无效，请检查配置！")
        if self.__config["saucenaoApiKey"] == "balabala":
            logger.warning("saucenaoApiKey无效，请检查配置！")
        if self.__config["txAppId"] == "1234567890":
            logger.warning("txAppId无效，请检查配置！")
        if self.__config["txAppKey"] == "ABCDEFGHIJKLMN":
            logger.warning("txAppKey无效，请检查配置！")
        if self.__config["loliconApiKey"] == "loliconApiKey":
            logger.warning("loliconApiKey无效，请检查配置！")
        if self.__config["wolframAlphaKey"] == "wolframAlphaKey":
            logger.warning("wolframAlphaKey无效，请检查配置！")
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

    def get_saya(self):
        return self.__saya
