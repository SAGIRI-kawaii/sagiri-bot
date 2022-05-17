from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup

from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from sagiri_bot.core.app_core import AppCore
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Forward, ForwardNode

config = AppCore.get_core_instance().get_config()
proxy = config.proxy if config.proxy != "proxy" else ''


async def search(*, keyword: Optional[str] = None, data_bytes: Optional[bytes] = None) -> MessageChain:
    search_url = "https://xslist.org/search?lg=en&query="
    pic_search_url = "https://xslist.org/search/pic"
    if not keyword and not data_bytes:
        raise ValueError("You should give keyword or data_bytes!")
    elif keyword:
        keyword = keyword.strip()
        async with get_running(Adapter).session.get(search_url + keyword, proxy=proxy) as resp:
            html = await resp.text()
    elif data_bytes:
        async with get_running(Adapter).session.post(
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
        async with get_running(Adapter).session.get(avatar, proxy=proxy) as resp:
            avatar = await resp.read()
        msgs.append(
            MessageChain([
                Image(data_bytes=avatar),
                Plain('\n'),
                Plain(li.find("h3").find("a")["title"]),
                Plain('\n'),
                Plain(li.find("p").get_text().replace("<br />", '\n'))
            ])
        )
    return msgs[0] if len(msgs) == 1 else MessageChain([
        Forward([
            ForwardNode(
                senderId=config.bot_qq,
                time=datetime.now(),
                senderName="SAGIRI BOT",
                messageChain=msg,
            ) for msg in msgs
        ])
    ])
