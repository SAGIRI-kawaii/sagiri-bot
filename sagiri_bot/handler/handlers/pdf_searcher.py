import re
import aiohttp
from bs4 import BeautifulSoup
from aiohttp import TCPConnector

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult, SpacePolicy

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("PDFSearcher")
channel.author("SAGIRI-kawaii")
channel.description("可以搜索pdf的插件，在群中发送 `pdf 书名` 即可")

core = AppCore.get_core_instance()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ''


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("pdf").space(SpacePolicy.FORCE), RegexMatch(r".+") @ "keyword"])],
        decorators=[
            FrequencyLimit.require("pdf_searcher", 4),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH)

        ]
    )
)
async def pdf_searcher(app: Ariadne, message: MessageChain, group: Group, keyword: RegexResult):
    base_url = "https://zh.1lib.tw"
    keyword = keyword.result.asDisplay().strip()
    url = f"{base_url}/s/?q={keyword}"
    async with aiohttp.ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
        async with session.get(url=url, proxy=proxy) as resp:
            html = await resp.read()
    soup = BeautifulSoup(html, "html.parser")
    try:
        divs = soup.find(
            "div", {"id": "searchResultBox"}
        ).find_all(
            "div", {"class": "resItemBox resItemBoxBooks exactMatch"}
        )
    except AttributeError:
        await app.sendGroupMessage(group, MessageChain(f"请检查{base_url}是否可以正常访问！若不可以请检查代理是否正常，若代理正常可能为域名更换，请向仓库提出PR"))
        return
    count = 0
    books = []
    text = "搜索到以下结果：\n\n"
    for div in divs:
        count += 1
        if count > 5:
            break
        name = div.find("h3").get_text().strip()
        href = div.find("h3").find("a", href=True)["href"]
        # cover = div.find("table").find("img")["src"]
        first_div = div.find("table").find("table").find("div")
        publisher = first_div.get_text().strip() if re.search('.*?title="Publisher".*?', str(first_div)) else None
        authors = div.find("div", {"class": "authors"}).get_text().strip()

        text += f"{count}.\n"
        text += f"名字：{name}\n"
        text += f"作者：{authors}\n" if authors else ""
        text += f"出版社：{publisher}\n" if publisher else ""
        text += f"页面链接：{base_url + href}\n\n"

        books.append({
            "name": name,
            # "cover": cover,
            "href": base_url + href,
            "publisher": publisher,
            "authors": authors
        })

    if not books:
        text = "未搜索到结果呢 >A<\n要不要换个关键词试试呢~"
    await app.sendGroupMessage(group, MessageChain(text), quote=message.getFirst(Source))
