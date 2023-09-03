from graia.saya import Channel
from graiax.shortcut.saya import listen, decorate

from avilla.core import Context, MessageChain, MessageReceived

from shared.models.plugin import PluginMeta
from shared.utils.control import FunctionCall, Function, SceneSwitch, Distribute

channel = Channel.current()
meta = PluginMeta.from_path(__file__)
channel.meta = meta.to_saya_meta()

DEFAULT_ECHO = "Hello World by SAGIRI-BOT V5.0.0 powered by Avilla"

@listen(MessageReceived)
@decorate(Distribute.distribute())
@decorate(SceneSwitch.check())
@decorate(Function.require(channel.module))
@decorate(FunctionCall.record("echo"))
async def hello(ctx: Context, message: MessageChain):
    if message.startswith("/echo"):
        await ctx.scene.send_message(DEFAULT_ECHO)
