import aiohttp
import asyncio
from loguru import logger

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast import Broadcast
from graia.ariadne.exception import AccountMuted
from graia.broadcast.interrupt.waiter import Waiter
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

from sagiri_bot.config import GlobalConfig
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.internal_utils import get_command
from sagiri_bot.internal_utils import MessageChainUtils
from sagiri_bot.internal_utils import group_setting, sec_to_str
from sagiri_bot.control import (
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


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    get_command(__file__, channel.module),
                    RegexMatch(r"[\s]+", optional=True),
                    ElementMatch(Image, optional=True) @ "image",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("bangumi_searcher", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def bangumi_searcher(
    app: Ariadne, group: Group, member: Member, source: Source, image: ElementResult
):
    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def image_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            if waiter_message.has(Image):
                return waiter_message.get_first(Image)
            else:
                return False

    if not await group_setting.get_setting(group.id, Setting.bangumi_search):
        return await app.send_group_message(group, MessageChain("搜番功能未开启呐~请联系管理员哦~"))

    if not image.matched:
        try:
            await app.send_message(group, MessageChain("请在30s内发送要处理的图片"), quote=source)
            image = await asyncio.wait_for(inc.wait(image_waiter), 30)
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
        async with session.post(
            url=url, proxy=proxy if proxy != "proxy" else ""
        ) as resp:
            result = await resp.json()
    # print(result)
    if result := result.get("result"):
        # print(json.dumps(result[0], indent=4))
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

        message = await MessageChainUtils.messagechain_to_img(
            MessageChain(
                [
                    Plain(text="搜索到结果：\n"),
                    Image(data_bytes=thumbnail_content),
                    Plain(text=f"番剧名: {title_native}\n"),
                    Plain(text=f"罗马音名: {title_romaji}\n"),
                    Plain(text=f"英文名: {title_english}\n"),
                    Plain(text=f"文件名: {file_name}\n"),
                    Plain(
                        text=f"时间: {sec_to_str(time_from)} ~ {sec_to_str(time_to)}\n"
                    ),
                    Plain(text=f"相似度: {similarity}%"),
                ]
            )
        )
        return message
    else:
        return MessageChain("没有查到结果呐~")
