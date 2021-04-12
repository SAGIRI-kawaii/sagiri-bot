import time
import asyncio
from loguru import logger

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Source, Plain


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton


@singleton
class ExceptionReSender:
    # task: [MessageItem, received_message, group, member, resendCount]
    __instance = None
    __first_init = False
    __tasks = []
    __listen_tasks = None
    max_retries = 5
    app = None

    def __new__(cls, app: GraiaMiraiApplication):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, app: GraiaMiraiApplication):
        if not self.__first_init:
            self.app = app
            ExceptionReSender.__first_init = True

    def get(self):
        if self.__tasks:
            return self.__tasks.pop(0)
        else:
            return None

    def addTask(self, task: list):
        self.__tasks.append(task)

    def getLen(self):
        return len(self.__tasks)


def exception_resender_listener(app: GraiaMiraiApplication, exception_resender_instance: ExceptionReSender, loop):
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
