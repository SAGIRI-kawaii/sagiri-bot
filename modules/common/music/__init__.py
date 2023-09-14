from graia.saya import Channel
from graiax.shortcut import listen, dispatch, decorate
from avilla.core import Context, MessageReceived, RawResource, Picture
from avilla.twilight.twilight import Twilight, WildcardMatch, RegexResult, ArgumentMatch, ArgResult

from shared.models.plugin import PluginMeta
from .utils import gen_desc_image, get_wyy_song
from shared.utils.control import FunctionCall, Function, SceneSwitch, Distribute

channel = Channel.current()
meta = PluginMeta.from_path(__file__)
channel.meta = meta.to_saya_meta()
DEFAULT_MUSIC_PLATFORM = "wyy"
DEFAULT_SEND_TYPE = "card"


@listen(MessageReceived)
@decorate(Distribute.distribute())
@decorate(SceneSwitch.check())
@decorate(Function.require(channel.module))
@decorate(FunctionCall.record("music"))
@dispatch(
    Twilight([
        meta.gen_match(),
        ArgumentMatch("-p", "-platform", type=str, choices=["qq", "wyy"], optional=True) @ "music_platform",
        ArgumentMatch("-t", "-type", type=str, choices=["card", "voice", "file"], optional=True) @ "send_type",
        WildcardMatch() @ "keyword"
    ])
)
async def music(ctx: Context, keyword: RegexResult, music_platform: ArgResult, send_type: ArgResult):
    music_platform = music_platform.result.display.strip() if music_platform.matched else DEFAULT_MUSIC_PLATFORM
    send_type = send_type.result if send_type.matched else DEFAULT_SEND_TYPE
    keyword = keyword.result
    song = await get_wyy_song(keyword)
    content = await gen_desc_image(song)
    await ctx.scene.send_message(Picture(RawResource(content)))