import aiohttp
import asyncio
import PIL.Image
import contextlib
from io import BytesIO
from pathlib import Path
from loguru import logger
from datetime import datetime
from aiohttp import TCPConnector

from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult

from shared.orm import orm
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)
from shared.models.config import GlobalConfig
from shared.orm.tables import Setting, LoliconData
from shared.models.group_setting import GroupSetting

channel = Channel.current()
channel.name("LoliconKeywordSearcher")
channel.author("SAGIRI-kawaii")
channel.description("一个接入lolicon api的插件，在群中发送 `来点{keyword}[色涩瑟]图` 即可")

config = create(GlobalConfig)
group_setting = create(GroupSetting)
proxy = config.proxy if config.proxy != "proxy" else ""
image_cache = config.functions.get("lolicon", {}).get("image_cache")
data_cache = config.functions.get("lolicon", {}).get("data_cache")
cache_path = Path(config.functions.get("lolicon", {}).get("cache_path", ""))
cache18_path = Path(config.functions.get("lolicon", {}).get("cache18_path", ""))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("来点"),
                RegexMatch(r"[^\s]+") @ "keyword",
                RegexMatch(r"[色涩瑟]图$"),
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("lolicon_keyword_searcher", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SETU),
        ],
    )
)
async def lolicon_keyword_searcher(app: Ariadne, group: Group, source: Source, keyword: RegexResult):
    keyword = keyword.result.display
    msg_chain = await get_image(group, keyword)
    if msg_chain.only(Plain):
        return await app.send_group_message(group, msg_chain, quote=source)
    mode = await group_setting.get_setting(group, Setting.r18_process)
    r18 = await group_setting.get_setting(group, Setting.r18)
    if mode == "revoke" and r18:
        msg = await app.send_group_message(group, msg_chain, quote=source)
        await asyncio.sleep(20)
        with contextlib.suppress(UnknownTarget):
            await app.recall_message(msg)
    elif mode == "flash" and r18:
        await app.send_group_message(group, msg_chain.exclude(Image), quote=source)
        await app.send_group_message(group, MessageChain(msg_chain.get_first(Image).to_flash_image()))
    else:
        await app.send_group_message(group, msg_chain, quote=source)


async def get_image(group: Group, keyword: str) -> MessageChain:
    word_filter = ("&", "r18", "&r18", "%26r18")
    r18 = await group_setting.get_setting(group.id, Setting.r18)
    if any(i in keyword for i in word_filter):
        return MessageChain("你注个寄吧")
    url = f"https://api.lolicon.app/setu/v2?r18={1 if r18 else 0}&keyword={keyword}"
    async with aiohttp.ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
        async with session.get(url=url, proxy=proxy) as resp:
            result = await resp.json()
    logger.info(result)
    if result["error"]:
        return MessageChain(result["error"])
    if result["data"]:
        result = result["data"][0]
    else:
        return MessageChain(f"没有搜到有关{keyword}的图哦～有没有一种可能，你的xp太怪了？")

    if data_cache:
        await orm.insert_or_update(
            LoliconData,
            [LoliconData.pid == result["pid"], LoliconData.p == result["p"]],
            {
                "pid": result["pid"],
                "p": result["p"],
                "uid": result["uid"],
                "title": result["title"],
                "author": result["author"],
                "r18": result["r18"],
                "width": result["width"],
                "height": result["height"],
                "tags": "|".join(result["tags"]),
                "ext": result["ext"],
                "upload_date": datetime.utcfromtimestamp(
                    int(result["uploadDate"]) / 1000
                ),
                "original_url": result["urls"]["original"],
            },
        )

    info = f"title: {result['title']}\nauthor: {result['author']}\nurl: {result['urls']['original']}"
    file_name = result["urls"]["original"].split("/").pop()
    base_path = cache18_path if r18 else cache_path
    file_path = base_path / file_name

    if file_path.exists():
        return MessageChain([
            Plain(text=f"你要的{keyword}涩图来辣！\n"),
            Image(path=file_path),
            Plain(text=f"\n{info}"),
        ])
    async with aiohttp.ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
        async with session.get(url=result["urls"]["original"], proxy=proxy) as resp:
            img_content = await resp.read()
    if image_cache and base_path.exists():
        image = PIL.Image.open(BytesIO(img_content))
        image.save(file_path)
    return MessageChain([
        Plain(text=f"你要的{keyword}涩图来辣！\n"),
        Image(data_bytes=img_content),
        Plain(text=f"\n{info}"),
    ])
