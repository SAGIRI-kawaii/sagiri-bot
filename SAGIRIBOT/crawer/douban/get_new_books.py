import aiohttp
from bs4 import BeautifulSoup
import asyncio

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.basics.tools import text2piiic_with_link


async def get_douban_new_books() -> list:
    url = "https://book.douban.com/latest?icn=index-latestbook-all"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            html = await resp.read()
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"id": "content"})
    fictitious = div.find("div", {"class": "article"})
    non_fictitious = div.find("div", {"class": "aside"})
    fictitious_lis = fictitious.find_all("li")
    non_fictitious_lis = non_fictitious.find_all("li")
    fictitiou_books = []
    non_fictitiou_books = []
    count = 0
    for fictitious_li in fictitious_lis:
        count += 1
        if count > 3:
            count = 0
            break
        name = fictitious_li.find("h2").find("a").get_text().strip()
        href = fictitious_li.find("h2").find("a", href=True)["href"]
        cover = fictitious_li.find("a", {"class": "cover"}, href=True).find("img")["src"]
        rating = fictitious_li.find("p", {"class": "rating"}).get_text().strip()
        rating = rating if rating else "尚无评价"
        publishment = fictitious_li.find("p", {"class": "color-gray"}).get_text().strip()
        detail = fictitious_li.find("p", {"class": "detail"}).get_text().strip()
        fictitiou_books.append({
            "name": name,
            "cover": cover,
            "href": href,
            "rating": rating,
            "publishment": publishment,
            "detail": detail
        })
        # print(name, href, cover, rating, publishment, detail, sep="\n", end="\n\n")

    for non_fictitious_li in non_fictitious_lis:
        count += 1
        if count > 3:
            break
        name = non_fictitious_li.find("h2").find("a").get_text().strip()
        href = non_fictitious_li.find("h2").find("a", href=True)["href"]
        cover = non_fictitious_li.find("a", {"class": "cover"}, href=True).find("img")["src"]
        rating = non_fictitious_li.find("p", {"class": "rating"}).get_text().strip()
        rating = rating if rating else "尚无评价"
        publishment = non_fictitious_li.find("p", {"class": "color-gray"}).get_text().strip()
        detail = non_fictitious_li.find_all("p")[2].get_text().strip()
        non_fictitiou_books.append({
            "name": name,
            "cover": cover,
            "href": href,
            "rating": rating,
            "publishment": publishment,
            "detail": detail
        })

    text = ""
    for book in fictitiou_books:
        text += f"书名：{book['name']}\n"
        text += f"评分：{book['rating']}\n"
        text += f"信息：{book['publishment']}\n"
        text += f"描述：{book['detail']}\n"
        text += f"链接：{book['href']}\n"

    for book in non_fictitiou_books:
        text += f"书名：{book['name']}\n"
        text += f"评分：{book['rating']}\n"
        text += f"信息：{book['publishment']}\n"
        text += f"描述：{book['detail']}\n"
        text += f"链接：{book['href']}\n"

    pics_path = await text2piiic_with_link(text=text)
    msg = [Plain(text="新书速递：\n\n")]
    for path in pics_path:
        msg.append(Image.fromLocalFile(path))
    # img.save("./statics/temp/tempPDFSearch.png")
    return [
        "quoteSource",
        MessageChain.create(msg)
    ]


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_douban_new_books())
