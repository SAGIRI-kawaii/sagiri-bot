from pathlib import Path

from graia.saya import Channel
from avilla.twilight.twilight import Twilight, FullMatch, WildcardMatch, ResultValue
from graiax.shortcut.saya import listen, decorate, dispatch
from avilla.core import Context, Message, MessageReceived, Picture, RawResource, MessageChain

from shared.models.plugin import PluginMeta
from shared.utils.text2img import template2img, PageOption
from shared.utils.control import FunctionCall, Function, SceneSwitch, Distribute

channel = Channel.current()
meta = PluginMeta.from_path(__file__)
channel.meta = meta.to_saya_meta()


@listen(MessageReceived)
@decorate(Distribute.distribute())
@decorate(SceneSwitch.check())
@decorate(Function.require(channel.module))
@decorate(FunctionCall.record("user_info"))
@dispatch(Twilight([FullMatch("/info"), WildcardMatch(optional=True) @ "qq"]))
async def user_info(ctx: Context, message: Message, qq: MessageChain = ResultValue()):
    qq = str(qq).strip()
    qid = qq if qq.isdigit() else message.sender['member'] 
    await ctx.scene.send_message(
        Picture(RawResource(
            await template2img(
                (Path(__file__).parent / "template2.html").read_text(), 
                {"img_url": f"https://q1.qlogo.cn/g?b=qq&nk={qid}&s=640"},
                extra_page_option=PageOption(viewport={'width': 1000, 'height': 600})
            )
        ))
    )
