import re

from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, GroupMessage, Member
from graia.ariadne.message.parser.twilight import WildcardMatch, RegexResult, ArgResult, ArgumentMatch

from core import Sagiri
from shared.utils.text2img import md2img
from shared.utils.module_related import get_command
from .conversation_manager import ConversationManager
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute,
    Config
)

channel = Channel.current()
channel.name("ChatGPT")
channel.author("SAGIRI-kawaii")
channel.description("一个接入 ChatGPT 的插件，在群中发送 `/chat 内容` 即可")
config = create(Sagiri).config
proxy = config.proxy if config.proxy != "proxy" else None
session_token = config.functions.get("openai_cookie")
manager = ConversationManager()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-n", "-new", action="store_true", optional=True) @ "new_thread",
                ArgumentMatch("-t", "-text", action="store_true", optional=True) @ "text",
                WildcardMatch().flags(re.DOTALL) @ "content",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Config.require("functions.openai_cookie"),
            FrequencyLimit.require("chat_gpt", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def chat_gpt(
    app: Ariadne,
    group: Group,
    member: Member,
    source: Source,
    new_thread: ArgResult,
    text: ArgResult,
    content: RegexResult
):
    if new_thread.matched:
        manager.new(group, member)
    response = await manager.send_message(group, member, content.result.display.strip())
    if text.matched:
        await app.send_group_message(group, MessageChain(response), quote=source)
    else:
        await app.send_group_message(
            group, MessageChain(Image(data_bytes=await md2img(response, use_proxy=True))), quote=source
        )
