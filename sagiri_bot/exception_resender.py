import time
import asyncio
from loguru import logger

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Plain


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton


@singleton
class ExceptionReSender(object):
    """
        错误重发模块，用于捕获发送失败的消息并进行重发，默认最大进行5次重发

        Attributes:
            app: Ariadne实例
            max_retries: 最大重试次数
    """
    # task: [MessageItem, received_message, group, member, resendCount]
    __instance = None
    __first_init = False
    __tasks = []
    __listen_tasks = None
    max_retries: int = 5
    app: Ariadne = None

    def __new__(cls, app: Ariadne, max_retries: int = 5):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, app: Ariadne = None, max_retries: int = 5):
        if not self.__first_init:
            self.app = app
            self.max_retries = max_retries
            ExceptionReSender.__first_init = True

    @classmethod
    def get_instance(cls):
        if cls.__instance:
            return cls.__instance
        else:
            raise ExceptionReSenderNotInitialized()

    def get(self):
        if self.__tasks:
            return self.__tasks.pop(0)
        else:
            return None

    def addTask(self, task: list):
        self.__tasks.append(task)

    def getLen(self):
        return len(self.__tasks)


def exception_resender_listener(app: Ariadne, exception_resender_instance: ExceptionReSender, loop):
    while True:
        task = exception_resender_instance.get()
        if task:
            logger.warning("task catched! " + "len:" + str(exception_resender_instance.getLen()) + "task: " + str(task))
            try:
                asyncio.run_coroutine_threadsafe(task[0].strategy.send(app, task[0].message, task[1], task[2], task[3]), loop)
                logger.success(f"task resend seccess! task: {str(task)}")
            except Exception:
                task[4] += 1
                if task[4] <= exception_resender_instance.max_retries:
                    exception_resender_instance.addTask(task)
                else:
                    logger.error("Maximum number of retries exceeded! Task cancelled!")
                    asyncio.run_coroutine_threadsafe(app.sendGroupMessage(task[4], MessageChain.create([
                        Plain(text="Maximum number of retries exceeded! Task cancelled!")
                    ]), quote=task[1][Source][0]), loop)
        time.sleep(2)


class ExceptionReSenderNotInitialized(Exception):
    """ 错误重发模块未实例化 """
