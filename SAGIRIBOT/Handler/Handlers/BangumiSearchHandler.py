import time
import json
import aiohttp
from loguru import logger
from PIL import Image as IMG
from urllib.parse import quote

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.application.exceptions import AccountMuted
from graia.broadcast.interrupt import InterruptControl
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage
from graia.application.message.elements.internal import Plain, Image, At, Source

from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.utils import MessageChainUtils
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.utils import get_setting, sec_to_str
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.ORM.AsyncORM import Setting, UserCalledCount
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def bangumi_search_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await BangumiSearchHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class BangumiSearchHandler(AbstractHandler):
    __name__ = "BangumiSearchHandler"
    __description__ = "一个可以根据图片搜索番剧的Handler"
    __usage__ = "在群中发送 `搜番` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "搜番":
            await update_user_call_count_plus1(group, member, UserCalledCount.search, "search")
            if not await get_setting(group.id, Setting.bangumi_search):
                return MessageItem(MessageChain.create([Plain(text="搜番功能未开启呐~请联系管理员哦~")]), Normal(GroupStrategy()))
            try:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(member.id), Plain("请在30秒内发送要搜索的图片呐~")
                ]))
            except AccountMuted:
                logger.error(f"Bot 在群 <{group.name}> 被禁言，无法发送！")
                return None

            image_get = None
            message_received = None

            @Waiter.create_using_function([GroupMessage])
            def waiter(
                    event: GroupMessage, waiter_group: Group,
                    waiter_member: Member, waiter_message: MessageChain
            ):
                nonlocal image_get
                nonlocal message_received
                if time.time() - start_time < 30:
                    if all([
                        waiter_group.id == group.id,
                        waiter_member.id == member.id,
                        len(waiter_message[Image]) == len(waiter_message.__root__) - 1
                    ]):
                        image_get = True
                        message_received = waiter_message
                        return event
                else:
                    logger.warning("等待用户超时！BangumiSearchHandler进程推出！")
                    return event

            bcc = AppCore.get_core_instance().get_bcc()
            inc = InterruptControl(bcc)
            start_time = time.time()
            await inc.wait(waiter)
            if image_get:
                logger.success("收到用户图片，启动搜索进程！")
                try:
                    await app.sendGroupMessage(
                        group,
                        await BangumiSearchHandler.search_bangumi(message_received[Image][0]),
                        quote=message_received[Source][0]
                    )
                except AccountMuted:
                    logger.error(f"Bot 在群 <{group.name}> 被禁言，无法发送！")
                    pass
            return None
        else:
            return None

    @staticmethod
    async def search_bangumi(img: Image) -> MessageChain:
        url = f"https://api.trace.moe/search?anilistInfo&url={img.url}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url) as resp:
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
                MessageChain.create([
                    Plain(text="搜索到结果：\n"),
                    Image.fromUnsafeBytes(thumbnail_content),
                    Plain(text=f"番剧名: {title_native}\n"),
                    Plain(text=f"罗马音名: {title_romaji}\n"),
                    Plain(text=f"英文名: {title_english}\n"),
                    Plain(text=f"文件名: {file_name}\n"),
                    Plain(text=f"时间: {sec_to_str(time_from)} ~ {sec_to_str(time_to)}\n"),
                    Plain(text=f"相似度: {similarity}%"),
                ])
            )
            return message
        else:
            return MessageChain.create([Plain(text="没有查到结果呐~")])
