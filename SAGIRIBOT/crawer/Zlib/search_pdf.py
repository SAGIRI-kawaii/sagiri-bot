import aiohttp
from bs4 import BeautifulSoup
import re

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.basics.tools import text2piiic
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting


async def search_pdf(group_id: int, keyword: str) -> list:
    url = f"https://zh.1lib.us/s/?q={keyword}"
    base_url = "https://zh.1lib.us"
    async with aiohttp.ClientSession() as session:
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

        # async with aiohttp.ClientSession() as session:
        #     async with session.get(url=base_url + href) as resp:
        #         html = await resp.read()
        #
        # re_res = re.findall(r'<a class="btn btn-primary dlButton addDownloadedBook" href="(.*?)"', str(html), re.S)
        # download_href = re_res[0] if re_res else None

        text += f"{count}.\n"
        text += f"名字：{name}\n"
        text += f"作者：{authors}\n"
        text += f"出版社：{publisher}\n"
        text += f"页面链接：{base_url + href}\n\n"

        books.append({
            "name": name,
            "href": base_url + href,
            "publisher": publisher,
            "authors": authors,
            # "download_href": base_url + download_href
        })

        print(name, href, publisher, authors, sep="\n", end="\n\n")

    if not books:
        text = "未搜索到结果呢 >A<\n要不要换个关键词试试呢~"

    long_text_setting = await get_setting(group_id, "longTextType")
    if long_text_setting == "img":
        img = text2piiic(string=text, poster="", length=max(len(x) for x in text.split("\n")))
        img.save("./statics/temp/tempPDFSearch.png")
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile("./statics/temp/tempPDFSearch.png")
            ])
        ]
    elif long_text_setting == "text":
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=text)
            ])
        ]
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="数据库 longTextType 项出错！请检查！")
            ])
        ]

