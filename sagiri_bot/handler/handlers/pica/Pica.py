import asyncio
import hmac
import json
import time
import uuid
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple, Union

import aiohttp
from aiohttp import TCPConnector
from creart import create
from loguru import logger
from PIL import Image as IMG
from yarl import URL

from sagiri_bot.config import GlobalConfig

BASE_PATH = Path(__file__).parent
CACHE_PATH = BASE_PATH / "cache" / "download"
global_url = URL("https://picaapi.picacomic.com/")
api_key = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
uuid_s = str(uuid.uuid4()).replace("-", "")
header = {
    "api-key": "C69BAF41DA5ABD1FFEDC6D2FEA56B",
    "app-channel": "2",
    "app-version": "2.2.1.3.3.4",
    "app-uuid": "defaultUuid",
    "image-quality": "original",
    "app-platform": "android",
    "app-build-version": "44",
    "Content-Type": "application/json; charset=UTF-8",
    "User-Agent": "okhttp/3.8.1",
    "accept": "application/vnd.picacomic.com.v1+json",
    "time": 0,
    "nonce": "",
    "signature": "encrypt",
}
path_filter = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]

config = create(GlobalConfig)
loop = create(asyncio.AbstractEventLoop)
proxy = config.proxy if config.proxy != "proxy" else ""
pica_config = config.functions.get("pica", {})
username = pica_config.get("username", None)
password = pica_config.get("password", None)
compress_password = pica_config.get("compress_password", "i_luv_sagiri")
DOWNLOAD_CACHE = pica_config.get("download_cache", True)


class Pica:
    def __init__(self, account, pwd):
        CACHE_PATH.mkdir(parents=True, exist_ok=True)
        self.init = False
        self.account = account
        self.password = pwd
        self.header = header.copy()
        self.header["nonce"] = uuid_s
        asyncio.run_coroutine_threadsafe(self.check(), loop)

    @logger.catch
    async def check(self) -> Optional[bool]:
        try:
            token = await self.login()
            self.header["authorization"] = token
            self.init = True
            return True
        except aiohttp.ClientConnectorError:
            logger.error("proxy配置可能错误或失效，请检查")
        except KeyError:
            logger.error("pica 账号密码可能错误，请检查")

    def update_signature(
        self, url: Union[str, URL], method: Literal["GET", "POST"]
    ) -> dict:
        if isinstance(url, str):
            url = URL(url)
        ts = str(int(time.time()))
        temp_header = self.header.copy()
        temp_header["time"] = ts
        temp_header["signature"] = self.encrypt(url, ts, method)
        if method == "GET":
            temp_header.pop("Content-Type")
        return temp_header

    @staticmethod
    def encrypt(url: URL, ts, method):
        datas = [
            global_url,
            url.path[1:],
            ts,
            uuid_s,
            method,
            "C69BAF41DA5ABD1FFEDC6D2FEA56B",
            "2.2.1.3.3.4",
            "45",
        ]
        _src = Pica.__ConFromNative(datas)
        _key = Pica.__SigFromNative()
        return Pica.HashKey(_src, _key)

    @staticmethod
    def __ConFromNative(datas):
        return "".join(map(str, datas[1:6]))

    @staticmethod
    def __SigFromNative():
        return "~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn"

    @staticmethod
    def HashKey(src, key):
        app_secret = key.encode("utf-8")  # 秘钥
        data = src.lower().encode("utf-8")  # 数据
        return hmac.new(app_secret, data, digestmod=sha256).hexdigest()

    async def request(
        self, url: Union[str, URL], params: Optional[Dict[str, str]] = None
    ):
        temp_header = self.update_signature(url, "GET")
        data = json.dumps(params) if params else None
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(
                url=url, headers=temp_header, proxy=proxy, data=data
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def login(self):
        """登录获取token"""
        url = global_url / "auth" / "sign-in"
        send = {"email": self.account, "password": self.password}
        ret = await self.request(url, send)
        self.header["authorization"] = ret["data"]["token"]
        return self.header["authorization"]

    async def categories(self):
        """获取所有目录"""
        url = global_url / "categories"
        return (await self.request(url))["data"]["categories"]

    async def search(self, keyword: str):
        """关键词搜索"""
        url = global_url / "comics" / "search" % {"page": keyword, "q": 1}
        _return = []
        for q in range(1, 3):
            url = url % {"q": q}
            __res = (await self.request(url))["data"]["comics"]["docs"]
            _return += [
                {"name": __["title"], "id": __["_id"]}
                for __ in __res
                if __["likesCount"] < 200
                and (__["pagesCount"] / __["epsCount"] > 60 or __["epsCount"] > 10)
            ]
        return _return

    async def random(self):
        """随机本子"""
        url = global_url / "comics" / "random"
        return (await self.request(url))["data"]["comics"]

    async def rank(self, tt: Literal["H24", "D7", "D30"] = "H24"):
        """排行榜"""
        url = global_url / "comics" / "leaderboard" % {"ct": "VC", "tt": tt}
        return (await self.request(url))["data"]["comics"]

    async def comic_info(self, book_id: str):
        """漫画详情"""
        url = global_url / "comics" / book_id
        return (await self.request(url))["data"]["comics"]

    async def download_image(
        self, url: str, path: Optional[Union[str, Path]] = None
    ) -> bytes:
        temp_header = self.update_signature(url, "GET")
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(url=url, headers=temp_header, proxy=proxy) as resp:
                if resp.status != 200:
                    resp.raise_for_status()
                image_bytes = await resp.read()

        if path:
            Path(path).write_bytes(image_bytes)
        return image_bytes

    async def download_comic(self, book_id: str) -> Tuple[Path, str]:
        info = await self.comic_info(book_id)
        episodes = info["epsCount"]
        comic_name = f"{info['title']} - {info['author']}"
        tasks = []
        for char in path_filter:
            comic_name = comic_name.replace(char, " ")
        comic_path = CACHE_PATH / comic_name
        comic_path.mkdir(exist_ok=True)
        for episode in range(episodes):
            url = global_url / "comics" / book_id / "order" / str(episode + 1) / "pages"
            data = (await self.request(url))["data"]
            episode_title: str = data["ep"]["title"]
            episode_path = comic_path / episode_title
            episode_path.mkdir(exist_ok=True)
            for img in data["pages"]["docs"]:
                media = img["media"]
                img_url = f"{media['fileServer']}/static/{media['path']}"
                image_path: Path = episode_path / media["originalName"]
                if image_path.exists():
                    continue
                tasks.append(
                    asyncio.create_task((self.download_image(img_url, image_path)))
                )
        _ = await asyncio.gather(*tasks)
        return comic_path, comic_name


pica = Pica(username, password)
# print(loop.run_until_complete(pica.search("SAGIRI")))
# print(loop.run_until_complete(pica.categories()))
# print(loop.run_until_complete(pica.random()))
# print(loop.run_until_complete(pica.rank()))
# print(loop.run_until_complete(pica.comic_info("5ce4d819431b5d017ddc8199")))
# loop.run_until_complete(pica.download_comic("5821a1d55f6b9a4f93ef4a6b"))
