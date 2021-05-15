import time
import aiohttp
from loguru import logger

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.application.exceptions import AccountMuted
from graia.broadcast.interrupt import InterruptControl
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage
from graia.application.message.elements.internal import Source, Plain, At, Image

from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.utils import get_setting, get_config
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.ORM.AsyncORM import Setting, UserCalledCount
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.Core.Exceptions import AsyncioTasksGetResult
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

saucenao_cookie = get_config("saucenaoCookie")
saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await ImageSearchHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class ImageSearchHandler(AbstractHandler):
    """ 图片搜素Handler(saucenao) """
    __name__ = "ImageSearchHandler"
    __description__ = "一个可以搜索Pixiv图片的Handler"
    __usage__ = "在群中发送 `搜图` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "搜图":
            await update_user_call_count_plus1(group, member, UserCalledCount.search, "search")
            if not await get_setting(group.id, Setting.img_search):
                return MessageItem(MessageChain.create([Plain(text="搜图功能未开启呐~请联系管理员哦~")]), Normal(GroupStrategy()))
            try:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(member.id), Plain("请在30秒内发送要搜索的图片呐~(仅支持pixiv图片搜索呐！)")
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
                    logger.warning("等待用户超时！ImageSearchHandler进程推出！")
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
                        await ImageSearchHandler.search_image(message_received[Image][0]),
                        quote=message_received[Source][0]
                    )
                except AccountMuted:
                    logger.error(f"Bot 在群 <{group.name}> 被禁言，无法发送！")
                    pass

            return None
        else:
            return None

    @staticmethod
    async def search_image(img: Image) -> MessageChain:
        # url for headers
        url = "https://saucenao.com/search.php"

        # picture url
        pic_url = img.url

        # json requesting url
        url2 = f"https://saucenao.com/search.php?db=999&output_type=2&testmode=1&numres=1&url={pic_url}"

        # data for posting.
        payload = {
            "url": pic_url,
            "numres": 1,
            "testmode": 1,
            "db": 999,
            "output_type": 2,
        }

        # header to fool the website.
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Referer": url,
            "Origin": "https://saucenao.com",
            "Host": "saucenao.com",
            "cookie": saucenao_cookie
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=payload) as resp:
                json_data = await resp.json()

        if json_data["header"]["status"] == -1:
            return MessageChain.create([
                Plain(text=f"错误：{json_data['header']['message']}")
            ])

        if not json_data["results"]:
            return MessageChain.create([
                Plain(text="没有搜索到结果呐~")
            ])

        result = json_data["results"][0]
        header = result["header"]
        data = result["data"]

        async with aiohttp.ClientSession() as session:
            async with session.get(url=header["thumbnail"]) as resp:
                img_content = await resp.read()

        similarity = header["similarity"]
        data_str = f"搜索到如下结果：\n\n相似度：{similarity}%\n"
        for key in data.keys():
            if isinstance(data[key], list):
                data_str += (f"\n{key}:\n    " + "\n".join(data[key]) + "\n")
            else:
                data_str += f"\n{key}:\n    {data[key]}\n"
        return MessageChain.create([
            Image.fromUnsafeBytes(img_content),
            Plain(text=f"\n{data_str}")
        ])
