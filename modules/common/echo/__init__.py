from graia.saya import Channel
from graiax.shortcut.saya import listen, decorate

from avilla.core import Context, MessageChain, MessageReceived

from shared.utils.control import FunctionCall

channel = Channel.current()

DEFAULT_ECHO = "Hello World by SAGIRI-BOT V5.0.0 powered by Avilla"

@listen(MessageReceived)
@decorate(FunctionCall.record("echo"))
async def hello(cx: Context, message: MessageChain):
    if message.startswith("/echo"):
        await cx.scene.send_message(message.removeprefix("/echo", copy=True).removeprefix(" ") or DEFAULT_ECHO)