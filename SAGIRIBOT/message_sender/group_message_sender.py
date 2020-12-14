import asyncio

from graia.application.event.mirai import Group
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import MessageChain


def group_message_sender(app: GraiaMiraiApplication, group: Group, msg: MessageChain, loop) -> None:
    asyncio.run_coroutine_threadsafe(app.sendGroupMessage(group, msg), loop)
