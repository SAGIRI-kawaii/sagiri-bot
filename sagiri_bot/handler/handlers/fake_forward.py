import re
import random
from datetime import datetime

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.element import ForwardNode, Image, Plain, Forward, At

from sagiri_bot.utils import get_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("FakeForward")
channel.author("SAGIRI-kawaii")
channel.description("一个生成转发消息的插件，发送 '/fake [@目标] [内容]' 即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def fake_forward(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await FakeForward.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class FakeForward(AbstractHandler):
    __name__ = "FakeForward"
    __description__ = "转发消息生成器"
    __usage__ = "None"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("/fake "):
            content = "".join(i.text for i in message.get(Plain))[6:]
            if not message.has(At):
                return MessageItem(MessageChain.create([Plain(text="未指定目标！")]), Normal())
            sender = message.get(At)[0]
            forward_nodes = [
                ForwardNode(
                    senderId=sender.target,
                    time=datetime.now(),
                    senderName=(await app.getMember(group, sender.target)).name,
                    messageChain=MessageChain.create(Plain(text=content)),
                )
            ]
            return MessageItem(MessageChain.create(Forward(nodeList=forward_nodes)), Normal())
