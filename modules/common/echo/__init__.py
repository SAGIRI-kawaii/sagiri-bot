from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from avilla.core import Context, MessageChain, MessageReceived

channel = Channel.current()

DEFAULT_ECHO = "Hello World by SAGIRI-BOT V5.0.0 powered by Avilla"

@channel.use(ListenerSchema([MessageReceived]))
async def hello(cx: Context, message: MessageChain):
    if message.startswith("/echo"):
        await cx.scene.send_message(message.removeprefix("/echo", copy=True).removeprefix(" ") or DEFAULT_ECHO)