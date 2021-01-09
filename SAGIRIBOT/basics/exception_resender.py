from threading import Thread
import time
import asyncio
from asyncio.events import AbstractEventLoop

from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import Source
from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain


def singleton(cls):
    # 单下划线的作用是这个变量只能在当前模块里访问,仅仅是一种提示作用
    # 创建一个字典用来保存类的实例对象
    _instance = {}

    def _singleton(*args, **kwargs):
        # 先判断这个类有没有对象
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)  # 创建一个对象,并保存到字典当中
        # 将实例对象返回
        return _instance[cls]

    return _singleton


@singleton
class ExceptionReSender:
    # task: [command, message, received_message, message_info, group, resendCount]
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


async def revoke_process(app: GraiaMiraiApplication, task: list):
    msg = await app.sendGroupMessage(task[4], task[1])
    await asyncio.sleep(20)
    await app.revokeMessage(msg)


def exception_resender_listener(app: GraiaMiraiApplication, exception_resender_instance: ExceptionReSender, loop):
    while True:
        task = exception_resender_instance.get()
        # print("task: ", task)
        if task:
            print("task catched!")
            print("len:", exception_resender_instance.getLen())
            print("task: ", task)
            try:
                if len(task) > 1 and task[0] == "None":
                    asyncio.run_coroutine_threadsafe(app.sendGroupMessage(task[4], task[1]), loop)
                    # await app.sendGroupMessage(task[4], task[1])
                elif len(task) > 1 and task[0] == "AtSender":
                    asyncio.run_coroutine_threadsafe(app.sendGroupMessage(task[4], task[1]), loop)
                    # await app.sendGroupMessage(task[4], task[1])
                elif len(task) > 1 and task[0] == "quoteSource":
                    asyncio.run_coroutine_threadsafe(app.sendGroupMessage(task[4], task[1], quote=task[2][Source][0]), loop)
                    # await app.sendGroupMessage(task[4], task[1], quote=task[2][Source][0])
                elif len(task) > 1 and task[0] == "revoke":
                    asyncio.run_coroutine_threadsafe(revoke_process(app, task), loop)
                    # msg = asyncio.run_coroutine_threadsafe(app.sendGroupMessage(task[4], task[1]), loop)
                    # asyncio.run_coroutine_threadsafe(asyncio.sleep(20), loop)
                    # asyncio.run_coroutine_threadsafe(app.revokeMessage(msg.result()), loop)
                    # msg = await app.sendGroupMessage(task[4], task[1])
                    # await asyncio.sleep(20)
                    # await app.revokeMessage(msg)
            except Exception:
                task[5] += 1
                if task[5] <= exception_resender_instance.max_retries:
                    exception_resender_instance.addTask(task)
                else:
                    asyncio.run_coroutine_threadsafe(app.sendGroupMessage(task[4], MessageChain.create([
                        Plain(text="Maximum number of retries exceeded! Task cancelled!")
                    ]), quote=task[2][Source][0]), loop)
        time.sleep(1)
