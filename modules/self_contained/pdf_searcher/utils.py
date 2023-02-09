import re
import aiohttp
from yarl import URL
from pathlib import Path
from bs4 import BeautifulSoup
from aiohttp import TCPConnector

from creart import create

from .model import Book
from shared.models.config import GlobalConfig

config = create(GlobalConfig)
proxy = config.get_proxy()
pdf_config = config.functions.get("pdf", {})
base_url = pdf_config.get("base_url", "")
username = pdf_config.get("username")
password = pdf_config.get("password")
headers = {
    "authority": base_url.split("//")[-1].strip("/"),
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/109.0.0.0 Safari/537.36 "
}

cookie = None


async def get_cookie(force_refresh: bool = False) -> str:
    global cookie
    if not force_refresh and cookie:
        return cookie
    login_url = "https://singlelogin.me/rpc.php"
    login_data = {
        "isModal": True,
        "email": username,
        "password": password,
        "action": "login",
        "redirectUrl": "",
        "isSinglelogin": 1,
        "gg_json_mode": 1
    }
    async with aiohttp.ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
        async with session.post(login_url, data=login_data, proxy=proxy) as resp:
            cookies = {k: v.value for k, v in resp.cookies.items()}
        cookies = "; ".join([f"{i}={v}" for i, v in cookies.items()])
        cookie = cookies
        return cookie


async def get_books(keyword: str) -> list[Book]:
    url = URL(base_url) / "s" / f"?q={keyword}"
    headers["cookie"] = await get_cookie()
    async with aiohttp.ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
        async with session.get(url=url, proxy=proxy, headers=headers) as resp:
            html = await resp.read()
    soup = BeautifulSoup(html, "html.parser")
    try:
        divs = soup.find("div", {"id": "searchResultBox"}).find_all(
            "div", {"class": "resItemBox resItemBoxBooks exactMatch"}
        )
    except AttributeError:
        return []
    books = []
    for div in divs:
        name = div.find("h3").get_text().strip()
        href = div.find("h3").find("a", href=True)["href"]
        try:
            cover = div.find("table").find("img")["data-src"]
        except KeyError:
            cover = None
        first_div = div.find("table").find("table").find("div")
        publisher = (
            first_div.get_text().strip()
            if re.search('.*?title="Publisher".*?', str(first_div))
            else None
        )
        authors = div.find("div", {"class": "authors"}).get_text().strip()
        books.append(
            Book(
                name=name,
                base_url=base_url,
                cover=cover,
                href=str(URL(base_url) / href.strip("/")),
                publisher=publisher,
                authors=authors
            )
        )
    return books


async def download_book(book: Book, path: str | Path | None = None) -> tuple[str, bytes] | None:
    if path:
        path = Path(path)
    headers["cookie"] = await get_cookie()
    async with aiohttp.ClientSession() as session:
        async with session.get(book.href, headers=headers, proxy=proxy) as resp:
            html = await resp.read()
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div", {"class": "book-details-button"})
        download_a = div.find("a")
        name = download_a.get_text().strip()
        suffix, size = re.findall(r"\((.*?), (.*?)\)", name)[0]
        download_url = URL(base_url) / download_a["href"].strip("/")
        # print(suffix, size)
        async with session.get(download_url, headers=headers, proxy=proxy) as resp:
            content = await resp.read()
    if path:
        if path.is_dir():
            (path / f"{book.name}.{suffix.lower()}").write_bytes(content)
        elif path.is_file():
            path.write_bytes(content)
    else:
        return suffix.lower(), content
