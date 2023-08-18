import re
from loguru import logger
from contextlib import suppress
from sqlalchemy.sql import select
from sqlalchemy.exc import IntegrityError

from kayaku import create
from graia.saya import Channel
from graiax.shortcut.saya import listen, decorate, dispatch
from avilla.standard.core.application import ApplicationReady
from avilla.core import Context, MessageChain, MessageReceived, Message, Picture
from avilla.twilight.twilight import Twilight, FullMatch, RegexMatch, WildcardMatch, ResultValue, UnionMatch

from shared.database import get_interface
from shared.models.plugin import PluginMeta
from shared.utils.image import get_md5, get_image_type
from .utils import get_image, valid2send, gen_cache_path
from .models import GalleryConfig, GalleryTriggerWord, GallerySwitch
from shared.utils.control import FunctionCall, Function, SceneSwitch, Permission, PermissionLevel

channel = Channel.current()
meta = PluginMeta.from_path(__file__)
channel.meta = meta.to_saya_meta()
create(GalleryConfig)
DEFAULT_SEPARATOR = create(GalleryConfig).command_separator
RESPONSE_DICT = {
    "PermissionError": "你的权限不足哦",
    "IntervalError": "这群怎么这么活跃啊，歇会儿吧（",
    "GalleryClosed": "这个图库关闭了哦，别白费力气了捏"
}


@listen(MessageReceived)
@decorate(SceneSwitch.check())
@decorate(Function.require(channel.module))
async def keyword_detect(ctx: Context, message: Message):
    keyword = str(message.content)
    db = get_interface()
    if name := await db.select_first(select(GalleryTriggerWord.gallery).where(GalleryTriggerWord.keyword == keyword)):
        await FunctionCall.record("gallery").exec_target.callable(message)
        valid = await valid2send(message.scene, name)
        print(valid)
        if isinstance(valid, str):
            return await ctx.scene.send_message(RESPONSE_DICT[valid])
        gallerys = create(GalleryConfig, flush=True)
        if gallery := gallerys[name]:
            await ctx.scene.send_message(await get_image(name, gallery))


@listen(MessageReceived)
@decorate(Permission.require(PermissionLevel.USER))
@dispatch(Twilight([
    FullMatch("添加图库关键词"), 
    FullMatch(DEFAULT_SEPARATOR), 
    RegexMatch(r"[\w\W]+") @ "gallery_name", 
    FullMatch(DEFAULT_SEPARATOR), 
    WildcardMatch() @ "keyword"
]))
async def add_keyword(ctx: Context, gallery_name: MessageChain = ResultValue(), keyword: MessageChain = ResultValue()):
    gallery_name, keyword = str(gallery_name).strip(), str(keyword).strip()
    gallerys = create(GalleryConfig, flush=True)
    if not gallerys[gallery_name]:
        return await ctx.scene.send_message(f"不存在图库 <{gallery_name}>，已加载图库如下：{'，'.join([str(i) for i in gallerys.configs])}")
    db = get_interface()
    if config := await db.select_first(select(GalleryTriggerWord).where(GalleryTriggerWord.keyword == keyword)):
        return await ctx.scene.send_message(f"已存在相同主键！请在更改该关键词对应图库前删除旧的绑定！（旧绑定：{config.keyword} -> {config.gallery}）")
    _ = await db.add(GalleryTriggerWord(keyword=keyword, gallery=gallery_name))
    await ctx.scene.send_message(f"成功建立新绑定：{keyword} -> {gallery_name}")


@listen(MessageReceived)
@decorate(Permission.require(PermissionLevel.USER))
@dispatch(Twilight([
    FullMatch("删除图库关键词"), 
    FullMatch(DEFAULT_SEPARATOR), 
    WildcardMatch() @ "keyword"
]))
async def delete_keyword(ctx: Context, keyword: MessageChain = ResultValue()):
    keyword = str(keyword).strip()
    db = get_interface()
    if config := await db.select_first(select(GalleryTriggerWord).where(GalleryTriggerWord.keyword == keyword)):
        _ = await db.delete_exist(config)
        return await ctx.scene.send_message(f"成功移除旧绑定：{config.keyword} -> {config.gallery}")
    await ctx.scene.send_message(f"未找到关于{keyword}的绑定记录！")


@listen(MessageReceived)
@dispatch(Twilight(FullMatch("查看图库列表")))
async def show_galleries(ctx: Context):
    await ctx.scene.send_message(f"当前已加载图库：{'、'.join([str(i) for i in create(GalleryConfig).configs.keys()])}")


@listen(MessageReceived)
@dispatch(Twilight(
    FullMatch("查看图库关键词"),
    FullMatch(DEFAULT_SEPARATOR),
    WildcardMatch() @ "gallery_name"
))
async def show_galleries(ctx: Context, gallery_name: MessageChain = ResultValue()):
    db = get_interface()
    gallery_name = str(gallery_name).strip()
    res = await db.select_all(select(GalleryTriggerWord.keyword).where(GalleryTriggerWord.gallery == gallery_name))
    await ctx.scene.send_message(f"图库<{gallery_name}>关键词如下：{'、'.join(res)}")


@listen(MessageReceived)
@decorate(Permission.require(PermissionLevel.USER))
@dispatch(Twilight(
    UnionMatch("打开", "关闭") @ "operation",
    FullMatch("图库"),
    WildcardMatch() @ "gallery_name"
))
async def modify_gallery_switch(ctx: Context, message: Message, operation: MessageChain = ResultValue(), gallery_name: MessageChain = ResultValue()):
    operation, gallery_name = str(operation).strip(), str(gallery_name).strip()
    gallerys = create(GalleryConfig, flush=True)
    if not gallerys[gallery_name]:
        return await ctx.scene.send_message(f"不存在图库 <{gallery_name}>，已加载图库如下：{'，'.join([str(i) for i in gallerys.configs])}")
    create(GallerySwitch).modify(message.scene, gallery_name, operation == "打开")
    await ctx.scene.send_message(f"图库 <{gallery_name}> 开关已{operation}")


@listen(MessageReceived)
@decorate(Permission.require(PermissionLevel.USER))
@dispatch(Twilight([
    FullMatch("添加"),
    RegexMatch(".*") @ "gallery_name",
    FullMatch("图片"),
    WildcardMatch().flags(re.DOTALL)
]))
async def add_images(ctx: Context, message: Message, gallery_name: MessageChain = ResultValue()):
    gallery_name = str(gallery_name).strip()
    gallerys = create(GalleryConfig, flush=True)
    if not gallerys[gallery_name]:
        return await ctx.scene.send_message(f"不存在图库 <{gallery_name}>，已加载图库如下：{'，'.join([str(i) for i in gallerys.configs])}")
    if not (images := message.content.get(Picture)):
        return await ctx.scene.send_message("图片都没有，保存个鬼哦！")
    base_path = gen_cache_path(gallery_name, gallerys[gallery_name])
    for image in images:
        raw = await ctx.fetch(image.resource)
        img_type = get_image_type(raw)
        if img_type != "Unknown":
            save_path = base_path / f"{get_md5(raw)}.{img_type.lower()}"
            save_path.write_bytes(raw)
            logger.success(f"图片已缓存至{save_path.as_posix()}")
        else:
            save_path = base_path / f"{get_md5(raw)}.png"
            save_path.write_bytes(raw)
            logger.warning(f"未知类型图片！尝试保存为PNG格式")


@listen(ApplicationReady)
async def initialize():
    logger.info("正在初始化图库关键词数据")
    with suppress(IntegrityError):
        _ = await get_interface().add_many([GalleryTriggerWord(keyword=str(gallery), gallery=str(gallery)) for gallery in create(GalleryConfig).configs])
    logger.success("图库关键词数据初始化完成")
