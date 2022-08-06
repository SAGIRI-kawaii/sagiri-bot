from datetime import datetime

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import ForwardNode, Plain, Forward, At

from sagiri_bot.internal_utils import get_command
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("FakeForward")
channel.author("SAGIRI-kawaii")
channel.description("一个生成转发消息的插件，发送 '/fake [@目标] [内容]' 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            FrequencyLimit.require("fake_forward", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def fake_forward(app: Ariadne, message: MessageChain, group: Group):
    if message.display.startswith("/fake "):
        content = "".join(i.text for i in message.get(Plain))[6:]
        if not message.has(At):
            return await app.send_group_message(group, MessageChain("未指定目标！"))
        sender = message.get(At)[0]
        forward_nodes = [
            ForwardNode(
                sender_id=sender.target,
                time=datetime.now(),
                sender_name=(await app.get_member(group, sender.target)).name,
                message_chain=MessageChain(Plain(text=content)),
            )
        ]
        await app.send_group_message(group, MessageChain(Forward(node_list=forward_nodes)))
