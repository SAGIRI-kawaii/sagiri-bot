import time
import aiohttp
from loguru import logger

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import AccountMuted
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Source, Plain, At, Image
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import FullMatch, ElementMatch

from sagiri_bot.utils import get_setting
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.utils import update_user_call_count_plus
from sagiri_bot.orm.async_orm import Setting, UserCalledCount
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("ImageSearch")
channel.author("SAGIRI-kawaii")
channel.description("一个可以以图搜图的插件，在群中发送 `搜图` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）")

core = AppCore.get_core_instance()
bcc = core.get_bcc()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ''


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([FullMatch("搜图")]))]
    )
)
async def image_searcher(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await ImageSearch.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class ImageSearch(AbstractHandler):
    """ 图片搜素Handler(saucenao) """
    __name__ = "ImageSearcher"
    __description__ = "一个可以以图搜图的插件"
    __usage__ = "在群中发送 `搜图` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() in ("搜图", "以图搜图"):
            await update_user_call_count_plus(group, member, UserCalledCount.search, "search")
            if not await get_setting(group.id, Setting.img_search):
                return MessageItem(MessageChain.create([Plain(text="搜图功能未开启呐~请联系管理员哦~")]), Normal())
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

            inc = InterruptControl(bcc)
            start_time = time.time()
            await inc.wait(waiter)
            if image_get:
                logger.success("收到用户图片，启动搜索进程！")
                try:
                    await app.sendGroupMessage(
                        group,
                        await ImageSearch.search_image(message_received[Image][0]),
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
        # picture url
        pic_url = img.url

        url3 = f"https://saucenao.com/search.php?api_key={config.functions.get('saucenao_api_key')}&db=999" \
               f"&output_type=2&testmode=1&numres=10&url={pic_url} "

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.get(url=url3, proxy=proxy) as resp:
                json_data = await resp.json()

        if json_data["header"]["status"] == -1:
            return MessageChain.create([
                Plain(text=f"错误：{json_data['header']['message']}")
            ])

        if json_data["header"]["status"] == -2:
            return MessageChain.create([
                Plain(text=f"错误：24小时内搜索次数到达上限！")
            ])

        if not json_data["results"]:
            return MessageChain.create([
                Plain(text="没有搜索到结果呐~")
            ])

        result = json_data["results"][0]
        header = result["header"]
        data = result["data"]

        async with aiohttp.ClientSession() as session:
            async with session.get(url=header["thumbnail"], proxy=proxy) as resp:
                img_content = await resp.read()

        similarity = header["similarity"]
        data_str = f"搜索到如下结果：\n\n相似度：{similarity}%\n"
        for key in data.keys():
            if isinstance(data[key], list):
                data_str += (f"\n{key}:\n    " + "\n".join(data[key]) + "\n")
            else:
                data_str += f"\n{key}:\n    {data[key]}\n"
        return MessageChain.create([
            Image(data_bytes=img_content),
            Plain(text=f"\n{data_str}")
        ])
