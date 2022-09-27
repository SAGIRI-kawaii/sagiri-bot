import aiohttp
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup

from creart import create

from shared.models.config import GlobalConfig
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Forward, ForwardNode

config = create(GlobalConfig)
proxy = config.proxy if config.proxy != "proxy" else ""


async def search(
    *, keyword: Optional[str] = None, data_bytes: Optional[bytes] = None, account: int | None = None
) -> MessageChain:
    search_url = "https://xslist.org/search?lg=en&query="
    pic_search_url = "https://xslist.org/search/pic"
    if not keyword and not data_bytes:
        raise ValueError("You should give keyword or data_bytes!")
    elif keyword:
        keyword = keyword.strip()
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url + keyword, proxy=proxy) as resp:
                html = await resp.text()
    else:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                pic_search_url, data={"pic": data_bytes, "lg": "en"}, proxy=proxy
            ) as resp:
                html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    lis = soup.find_all("li")
    if not lis:
        return MessageChain(f"没有找到关于 {keyword} 的结果呢~换个关键词试试？")
    msgs = []
    for li in lis:
        avatar = li.find("img")["src"]
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar, proxy=proxy) as resp:
                avatar = await resp.read()
        msgs.append(
            MessageChain(
                [
                    Image(data_bytes=avatar),
                    Plain("\n"),
                    Plain(li.find("h3").find("a")["title"]),
                    Plain("\n"),
                    Plain(li.find("p").get_text().replace("<br />", "\n")),
                ]
            )
        )
    return msgs[0] if len(msgs) == 1 else MessageChain([
        Forward([
            ForwardNode(
                sender_id=account or config.default_account,
                time=datetime.now(),
                sender_name="SAGIRI BOT",
                message_chain=msg
            ) for msg in msgs
        ])
    ])
