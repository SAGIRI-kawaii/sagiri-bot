import aiohttp
import asyncio
from loguru import logger

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast import Broadcast
from graia.ariadne.exception import AccountMuted
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    ElementMatch,
    ElementResult,
)

from shared.utils.time import sec_format
from shared.utils.waiter import ImageWaiter
from shared.models.config import GlobalConfig
from shared.utils.text2img import messagechain2img
from shared.utils.module_related import get_command
from shared.models.group_setting import GroupSetting
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)


saya = Saya.current()
channel = Channel.current()

channel.name("BangumiSearcher")
channel.author("SAGIRI-kawaii")
channel.description("一个可以根据图片搜索番剧的插件，在群中发送 `搜番` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）")

bcc = create(Broadcast)
inc = InterruptControl(bcc)
proxy = create(GlobalConfig).proxy
proxy = proxy if proxy != "proxy" else ""
group_setting = create(GroupSetting)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r"[\s]+", optional=True),
                ElementMatch(Image, optional=True) @ "image",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("bangumi_searcher", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def bangumi_searcher(app: Ariadne, group: Group, member: Member, source: Source, image: ElementResult):

    if not image.matched:
        try:
            await app.send_message(group, MessageChain("请在30s内发送要处理的图片"), quote=source)
            image = await asyncio.wait_for(InterruptControl(create(Broadcast)).wait(ImageWaiter(group, member)), 30)
            if not image:
                return await app.send_group_message(
                    group, MessageChain("未检测到图片，请重新发送，进程退出"), quote=source
                )
        except asyncio.TimeoutError:
            return await app.send_group_message(
                group, MessageChain("图片等待超时，进程退出"), quote=source
            )
        except AccountMuted:
            logger.error(f"Bot 在群 <{group.name}> 被禁言，无法发送！")
            return None
    else:
        image = image.result
    logger.success("收到用户图片，启动搜索进程！")
    await app.send_group_message(group, MessageChain("已收到图片，正在进行搜索..."), quote=source)
    try:
        await app.send_group_message(group, await search_bangumi(image), quote=source)
    except AccountMuted:
        logger.error(f"Bot 在群 <{group.name}> 被禁言，无法发送！")


async def search_bangumi(img: Image) -> MessageChain:
    url = f"https://api.trace.moe/search?anilistInfo&url={img.url}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, proxy=proxy) as resp:
            result = await resp.json()
    if result := result.get("result"):
        title_native = result[0]["anilist"]["title"]["native"]
        title_romaji = result[0]["anilist"]["title"]["romaji"]
        title_english = result[0]["anilist"]["title"]["english"]
        file_name = result[0]["filename"]
        similarity = round(float(result[0]["similarity"]) * 100, 2)
        time_from = result[0]["from"]
        time_to = result[0]["to"]
        thumbnail_url = result[0]["image"]

        async with aiohttp.ClientSession() as session:
            async with session.get(url=thumbnail_url) as resp:
                thumbnail_content = await resp.read()

        return MessageChain(Image(data_bytes=await messagechain2img(
            MessageChain([
                Plain(text="搜索到结果：\n"),
                Image(data_bytes=thumbnail_content),
                Plain(text=f"番剧名: {title_native}\n"),
                Plain(text=f"罗马音名: {title_romaji}\n"),
                Plain(text=f"英文名: {title_english}\n"),
                Plain(text=f"文件名: {file_name}\n"),
                Plain(
                    text=f"时间: {sec_format(time_from)} ~ {sec_format(time_to)}\n"
                ),
                Plain(text=f"相似度: {similarity}%"),
            ]),
            img_single_line=True
        )))
    else:
        return MessageChain("没有查到结果呐~")
