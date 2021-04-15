import time
import json
import aiohttp
from loguru import logger
from PIL import Image as IMG
from urllib.parse import quote

from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.application.exceptions import AccountMuted
from graia.broadcast.interrupt import InterruptControl
from graia.application.message.chain import MessageChain
from graia.application.event.messages import GroupMessage, Group, Member
from graia.application.message.elements.internal import Plain, Image, At, Source

from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.utils import get_setting, sec_to_str
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.ORM.Tables import Setting, UserCalledCount
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.Core.Exceptions import AsyncioTasksGetResult
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.decorators import frequency_limit_require_weight_free


class BangumiSearchHandler(AbstractHandler):
    __name__ = "BangumiSearchHandler"
    __description__ = "一个可以根据图片搜索番剧的Handler"
    __usage__ = "在群中发送 `搜番` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "搜番":
            await update_user_call_count_plus1(group, member, UserCalledCount.search, "search")
            if not await get_setting(group.id, Setting.bangumi_search):
                set_result(message, MessageItem(MessageChain.create([Plain(text="搜番功能未开启呐~请联系管理员哦~")]), Normal(GroupStrategy())))
                # return MessageItem(MessageChain.create([Plain(text="搜番功能未开启呐~请联系管理员哦~")]), Normal(GroupStrategy()))
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
                        await self.search_bangumi(message_received[Image][0]),
                        quote=message_received[Source][0]
                    )
                    raise AsyncioTasksGetResult
                except AccountMuted:
                    logger.error(f"Bot 在群 <{group.name}> 被禁言，无法发送！")
                    pass
            return None
        else:
            return None
            # return await super().handle(app, message, group, member)

    @staticmethod
    async def search_bangumi(img: Image) -> MessageChain:
        url = f"https://trace.moe/api/search?url={img.url}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url) as resp:
                result = await resp.json()
        if docs := result["docs"]:
            print(json.dumps(docs[0], indent=4))
            title_chinese = docs[0]["title_chinese"]
            title_origin = docs[0]["title_chinese"]
            file_name = docs[0]["filename"]
            anilist_id = docs[0]["anilist_id"]
            time_from = docs[0]["from"]
            time_to = docs[0]["to"]

            t = docs[0]["at"]
            tokenthumb = docs[0]["tokenthumb"]
            thumbnail_url = f"https://media.trace.moe/image/{anilist_id}/{quote(file_name)}?t={t}&token={tokenthumb}&size=l"
            print(thumbnail_url)

            async with aiohttp.ClientSession() as session:
                async with session.get(url=thumbnail_url) as resp:
                    thumbnail_content = await resp.read()

            # url = f"https://anilist.co/anime/{anilist_id}"
            # async with aiohttp.ClientSession() as session:
            #     async with session.get(url=url) as resp:
            #         result = await resp.json()
            # result = result[0]
            # start_date = f"{result['startDate']['year']}-{result['startDate']['month']}-{result['startDate']['day']}"
            # end_date = f"{result['endDate']['year']}-{result['endDate']['month']}-{result['endDate']['day']}"
            # score = result["averageScore"]
            message = MessageChain.create([
                    Plain(text="搜索到结果：\n"),
                    Image.fromUnsafeBytes(thumbnail_content),
                    Plain(text=f"name: {title_origin}\n"),
                    Plain(text=f"Chinese name: {title_chinese}\n"),
                    Plain(text=f"file name: {file_name}\n"),
                    Plain(text=f"time: {sec_to_str(time_from)} ~ {sec_to_str(time_to)}\n"),
                    # Plain(text=f"score: {score}\n"),
                    # Plain(text=f"Broadcast date: {start_date} ~ {end_date}\n")
            ])
            return message
        else:
            return MessageChain.create([Plain(text="没有查到结果呐~")])
