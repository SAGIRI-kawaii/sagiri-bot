# -*- coding: utf-8 -*-
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain

import asyncio

from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Source
from message_process import group_message_process

from graia.application.event.messages import *

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080",
        authKey="1234567890",
        account=1785007019,
        websocket=True
    )
)


async def group_assist_process(received_message: MessageChain, message: list, group: Group) -> None:
    """
    Complete the auxiliary work that the function: message_process has not completed

    Args:
        received_message: Received message
        message: message list([what_needs_to_be_done, message_to_be_send])
        group: Group class from the receive message

    Examples:
        await group_assist_process(message, message_send, group)

    Return:
        None
    """
    if len(message) > 1 and message[0] == "None":
        await app.sendGroupMessage(group, MessageChain(__root__=[
            Plain("This message was sent by the new version of SAGIRI-Bot")
        ]))
        await app.sendGroupMessage(group, message[1])
    elif len(message) > 1 and message[0] == "AtSender":
        await app.sendGroupMessage(group, message[1])
    elif len(message) > 1 and message[0] == "quoteSource":
        await app.sendGroupMessage(group, message[1], quote=received_message[Source][0])


@bcc.receiver("FriendMessage")
async def friend_message_listener(
        app: GraiaMiraiApplication,
        friend: Friend,
        message: MessageChain
):
    await app.sendFriendMessage(friend, MessageChain(__root__=[
        Plain("你好！")
    ]))


@bcc.receiver("GroupMessage")
async def group_message_listener(
        app: GraiaMiraiApplication,
        group: Group,
        message: MessageChain,
        message_info: GroupMessage
):
    print("接收到组%s中来自%s的消息:%s" % (group.name, message_info.sender.name, message.asDisplay()))
    message_send = await group_message_process(message, message_info)
    print(message)
    await group_assist_process(message, message_send, group)


app.launch_blocking()
