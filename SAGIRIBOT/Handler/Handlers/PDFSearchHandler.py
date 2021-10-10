import re
import aiohttp
from bs4 import BeautifulSoup
from aiohttp import TCPConnector

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount, get_config

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def pdf_search_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await PDFSearchHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class PDFSearchHandler(AbstractHandler):
    __name__ = "PDFSearchHandler"
    __description__ = "可以搜索pdf的Handler"
    __usage__ = "在群中发送 `pdf 书名` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("pdf "):
            await update_user_call_count_plus1(group, member, UserCalledCount.search, "search")
            keyword = message.asDisplay()[4:]
            return await PDFSearchHandler.search_pdf(group, member, keyword)
        else:
            return None

    @staticmethod
    @frequency_limit_require_weight_free(4)
    async def search_pdf(group: Group, member: Member, keyword: str) -> MessageItem:
        base_url = "https://zh.sa1lib.org"
        url = f"{base_url}/s/?q={keyword}"
        proxy = get_config("proxy") if get_config("proxy") != "proxy_url" else ""
        async with aiohttp.ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
            async with session.get(url=url) as resp:
                html = await resp.read()
        soup = BeautifulSoup(html, "html.parser")
        divs = soup.find("div", {"id": "searchResultBox"}).find_all("div", {"class": "resItemBox resItemBoxBooks exactMatch"})
        count = 0
        books = []
        text = "搜索到以下结果：\n\n"
        for div in divs:
            count += 1
            if count > 5:
                break
            name = div.find("h3").get_text().strip()
            href = div.find("h3").find("a", href=True)["href"]
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
                "href": base_url + href,
                "publisher": publisher,
                "authors": authors
            })

        if not books:
            text = "未搜索到结果呢 >A<\n要不要换个关键词试试呢~"
        return MessageItem(MessageChain.create([Plain(text=text)]), QuoteSource(GroupStrategy()))
