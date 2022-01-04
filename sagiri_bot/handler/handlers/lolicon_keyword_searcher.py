import re
import os
import aiohttp
from io import BytesIO
from PIL import Image as IMG
from datetime import datetime

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import QuoteSource, Revoke
from sagiri_bot.utils import get_setting, update_user_call_count_plus
from sagiri_bot.orm.async_orm import Setting, UserCalledCount, LoliconData
from sagiri_bot.decorators import frequency_limit_require_weight_free, switch, blacklist

saya = Saya.current()
channel = Channel.current()

channel.name("LoliconKeywordSearcher")
channel.author("SAGIRI-kawaii")
channel.description("一个接入lolicon api的插件，在群中发送 `来点{keyword}[色涩瑟]图` 即可")

core = AppCore.get_core_instance()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ""
image_cache = config.data_related.get("lolicon_image_cache")
data_cache = config.data_related.get("lolicon_data_cache")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def lolicon_keyword_searcher(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await LoliconKeywordSearcher.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class LoliconKeywordSearcher(AbstractHandler):
    __name__ = "LoliconKeywordSearcher"
    __description__ = "一个接入lolicon api的插件"
    __usage__ = "在群中发送 `来点{keyword}[色涩瑟]图`"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(r"来点.+[色涩瑟]图", message.asDisplay()):
            await update_user_call_count_plus(group, member, UserCalledCount.setu, "setu")
            keyword = re.findall(r"来点(.*?)[色涩瑟]图", message.asDisplay(), re.S)[0]
            return await LoliconKeywordSearcher.get_image(group, member, keyword)
        else:
            return None

    @staticmethod
    @frequency_limit_require_weight_free(2)
    async def get_image(group: Group, member: Member, keyword: str):
        r18 = await get_setting(group.id, Setting.r18)
        url = f"https://api.lolicon.app/setu/v2?keyword={keyword}&r18={1 if r18 else 0}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                result = await resp.json()
        print(result)
        if result["error"]:
            return MessageItem(MessageChain.create([Plain(result["error"])]), QuoteSource())

        result = result["data"][0]

        if data_cache:
            await orm.insert_or_update(
                LoliconData,
                [
                    LoliconData.pid == result["pid"],
                    LoliconData.p == result["p"]
                ],
                {
                    "pid": result["pid"],
                    "p": result["p"],
                    "uid": result["uid"],
                    "title": result["title"],
                    "author": result["author"],
                    "r18": result["r18"],
                    "width": result["width"],
                    "height": result["height"],
                    "tags": '|'.join(result["tags"]),
                    "ext": result["ext"],
                    "upload_date": datetime.utcfromtimestamp(int(result["uploadDate"]) / 1000),
                    "original_url": result["urls"]["original"]
                }
            )

        info = f"title: {result['title']}\nauthor: {result['author']}\nurl: {result['urls']['original']}"
        file_name = result["urls"]["original"].split('/').pop()
        local_path = config.image_path.get("setu18") if r18 else config.image_path.get("setu")
        file_path = os.path.join(local_path, file_name)

        if os.path.exists(file_path):
            return MessageItem(
                MessageChain.create([
                    Plain(text=f"你要的{keyword}涩图来辣！\n"),
                    Image(path=file_path),
                    Plain(text=f"\n{info}")
                ]),
                QuoteSource() if not r18 else Revoke()
            )
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=result["urls"]["original"], proxy=proxy) as resp:
                    img_content = await resp.read()
            if image_cache:
                image = IMG.open(BytesIO(img_content))
                image.save(file_path)
            return MessageItem(
                MessageChain.create([
                    Plain(text=f"你要的{keyword}涩图来辣！\n"),
                    Image(data_bytes=img_content),
                    Plain(text=f"\n{info}")
                ]),
                QuoteSource() if not r18 else Revoke()
            )
