from meme_generator.meme import Meme
from meme_generator.manager import _memes
from meme_generator.download import check_resources

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.lifecycle import AccountLaunch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Source, Image, Plain, At
from graia.ariadne.event.message import Group, GroupMessage, Member
from graia.ariadne.message.parser.twilight import RegexResult, ElementResult, ArgResult

from shared.utils.text2img import md2img
from shared.utils.image import get_user_avatar
from .utils import gen_twilight, gen_depend, gen_doc
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()
channel.name("Memes")
channel.author("SAGIRI-kawaii")
checked = False


@channel.use(ListenerSchema(listening_events=[AccountLaunch]))
async def check():
    global checked
    if not checked:
        checked = True
        await check_resources()


for key, meme in _memes.items():
    @channel.use(
        ListenerSchema(
            listening_events=[GroupMessage],
            inline_dispatchers=[gen_twilight(meme)],
            decorators=[
                Distribute.distribute(),
                FrequencyLimit.require("memes", 1),
                Function.require(channel.module, notice=True),
                BlackListControl.enable(),
                UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
            ],
        )
    )
    async def _(
        app: Ariadne,
        member: Member,
        group: Group,
        args: RegexResult,
        source: Source,
        help_wanted: ArgResult,
        quote: ElementResult,
        meme_func: Meme = gen_depend(meme)
    ):
        if help_wanted.matched:
            return
        if quote.matched:
            args = await app.get_message_from_id(quote.result.id)
        else:
            args = args.result
        image_elements = []
        min_images = meme_func.params_type.min_images
        max_images = meme_func.params_type.max_images
        min_texts = meme_func.params_type.min_texts
        max_texts = meme_func.params_type.max_texts
        for i in args.__root__:
            if isinstance(i, Image):
                image_elements.append(await i.get_bytes())
            elif isinstance(i, At):
                image_elements.append(await get_user_avatar(i.target))
            elif isinstance(i, Plain) and i.text == "自己":
                image_elements.append(await member.get_avatar())
        text_elements = [i for i in "".join([i.text for i in args.__root__ if isinstance(i, Plain)]).split() if i]
        if not min_images <= len(image_elements) <= max_images:
            return await app.send_group_message(
                group,
                MessageChain(f"图片数量错误！要求为{min_images}-{max_images}张！(当前{len(image_elements)}张)"),
                quote=source
            )
        if not min_texts <= len(text_elements) <= max_texts:
            return await app.send_group_message(
                group,
                MessageChain(
                    f"文字数量错误！要求为{min_texts}-{max_texts}段！(当前{len(text_elements)}段)（以空格为间隔）"
                ),
                quote=source
            )
        await app.send_group_message(
            group,
            MessageChain(Image(data_bytes=(await meme_func(images=image_elements, texts=text_elements)).getvalue())),
            quote=source
        )

    @channel.use(
        ListenerSchema(
            listening_events=[GroupMessage],
            inline_dispatchers=[gen_twilight(meme, True)],
            decorators=[
                Distribute.distribute(),
                FrequencyLimit.require("memes", 1),
                Function.require(channel.module, notice=True),
                BlackListControl.enable(),
                UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
            ],
        )
    )
    async def _(app: Ariadne, group: Group, source: Source, help_wanted: ArgResult, meme_func: Meme = gen_depend(meme)):
        if help_wanted.matched:
            await app.send_group_message(
                group, MessageChain(Image(data_bytes=await md2img(await gen_doc(meme_func)))), quote=source
            )
