import asyncio

from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.broadcast import Broadcast
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.connection.util import UploadMethod
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, GroupMessage, Member
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult, SpacePolicy

from shared.utils.waiter import MessageWaiter
from shared.models.config import GlobalConfig
from shared.utils.module_related import get_command
from .utils import get_cookie, get_books, download_book
from shared.utils.control import (
    Distribute,
    Config,
    FrequencyLimit,
    Function,
    Permission,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()

channel.name("PDFSearcher")
channel.author("SAGIRI-kawaii")
channel.description("可以搜索pdf的插件，在群中发送 `pdf 书名` 即可")

config = create(GlobalConfig)
proxy = config.get_proxy()
pdf_config = config.functions.get("pdf", {})
base_url = pdf_config.get("base_url")
username = pdf_config.get("username")
password = pdf_config.get("password")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module).space(SpacePolicy.FORCE),
                RegexMatch(r".+") @ "keyword",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Config.require("functions.pdf.base_url"),
            Config.require("functions.pdf.username"),
            Config.require("functions.pdf.password"),
            Permission.require(Permission.GROUP_ADMIN),
            FrequencyLimit.require("pdf_searcher", 4),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def pdf_searcher(app: Ariadne, group: Group, member: Member, source: Source, keyword: RegexResult):
    keyword = keyword.result.display.strip()
    books = await get_books(keyword)
    if not books:
        return await app.send_group_message(group, "未搜索到结果或api失效 >A<", quote=source)
    await app.send_group_message(
        group,
        MessageChain(
            "搜索结果如下，若需要下载请在30秒内回复 `download 编号`:\n" +
            "\n\n".join([f"{i + 1}.\n{book.display}" for i, book in enumerate(books[:10])])
        ),
        quote=source
    )
    try:
        message = await asyncio.wait_for(InterruptControl(create(Broadcast)).wait(MessageWaiter(group, member)), 30)
    except asyncio.TimeoutError:
        return
    message = message.display.strip()
    if message.startswith("download ") and message[9:].isdigit():
        index = int(message[9:])
        if not 1 <= index <= len(books):
            return await app.send_group_message(group, f"不存在这个索引，只有 1-{len(books)} 呢")
        suffix, content = await download_book(books[index - 1])
        await app.upload_file(
            data=content,
            method=UploadMethod.Group,
            target=group,
            name=f"{books[index - 1].name}.{suffix}",
        )
