from multiprocessing import Queue
import time

from graia.application import GraiaMiraiApplication
from graia.application.event.mirai import Group
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import MessageChain

from SAGIRIBOT.message_sender.group_message_sender import group_message_sender


async def tasks_listener(app: GraiaMiraiApplication, tasks: Queue, loop) -> None:
    while 1:
        data = tasks.get()
        if data and len(data) > 2:
            if data[0] == "None":
                await app.sendGroupMessage(data[2], data[1])
                # group_message_sender(app, data[2], data[1], loop)
        # time.sleep(1)
