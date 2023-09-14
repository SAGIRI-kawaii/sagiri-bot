import re

from graia.saya import Channel
from graiax.shortcut import listen, dispatch, decorate
from avilla.core import Context, Picture, RawResource, MessageReceived, Message, MessageChain
from avilla.twilight.twilight import Twilight, WildcardMatch, ResultValue, ArgResult, ArgumentMatch

from .preset import preset_dict
from shared.utils.text2img import md2img
from shared.models.plugin import PluginMeta
from .conversation_manager import ConversationManager
from shared.utils.control import FunctionCall, Function, SceneSwitch, Distribute

channel = Channel.current()
meta = PluginMeta.from_path(__file__)
channel.meta = meta.to_saya_meta()
manager = ConversationManager()


@listen(MessageReceived)
@decorate(Distribute.distribute())
@decorate(SceneSwitch.check())
@decorate(Function.require(channel.module))
@decorate(FunctionCall.record("chat_gpt"))
@dispatch(
    Twilight([
        meta.gen_match(),
        ArgumentMatch("-n", "-new", action="store_true", optional=True) @ "new_thread",
        ArgumentMatch("-t", "-text", action="store_true", optional=True) @ "text",
        ArgumentMatch("-p", "-preset", optional=True) @ "preset",
        ArgumentMatch("--show-preset", action="store_true", optional=True) @ "show_preset",
        WildcardMatch().flags(re.DOTALL) @ "content",
    ])
)
async def chat_gpt(
    ctx: Context,
    message: Message,
    new_thread: ArgResult,
    text: ArgResult,
    preset: ArgResult,
    show_preset: ArgResult,
    content: MessageChain = ResultValue()
):
    if show_preset.matched:
        return await ctx.scene.send_message("当前内置预设：\n" + "\n".join([f"{i} ({v['name']})：{v['description']}" for i, v in preset_dict.items()]))
    if new_thread.matched:
        _ = await manager.new(message.sender, (preset.result.display.strip() if preset.matched else ""))
    response = await manager.send_message(message.sender, str(content))
    if text.matched:
        await ctx.scene.send_message(response)
    else:
        await ctx.scene.send_message(Picture(RawResource(await md2img(response))))
