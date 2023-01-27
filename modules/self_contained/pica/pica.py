import asyncio
import aiohttp
from loguru import logger
from typing import Literal
from dacite import from_dict

from creart import create

from shared.models.config import GlobalConfig
from .model import Comic, Category, PicaMethod, ComicInfo

path_filter = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]

config = create(GlobalConfig)
loop = create(asyncio.AbstractEventLoop)
proxy = config.proxy if config.proxy != "proxy" else ""
pica_config = config.functions.get("pica", {})
username = pica_config.get("username", "")
password = pica_config.get("password", "")
compress_password = pica_config.get("compress_password", "i_luv_sagiri")
DOWNLOAD_CACHE = pica_config.get("download_cache", True)


class Pica(PicaMethod):
    loop: asyncio.AbstractEventLoop
    init: bool = False

    def __init__(
        self,
        account: str,
        password: str,
        proxy: str | None = proxy,
        *,
        session: aiohttp.ClientSession | None = None
    ):
        super(Pica, self).__init__(session)
        self.account = account
        self.password = password
        self.proxy = proxy
        self.loop.run_until_complete(self.check())

    async def check(self) -> bool | None:
        if self.init:
            return True
        try:
            _ = await self.login()
            self.init = True
            return True
        except aiohttp.ClientConnectorError:
            logger.error("proxy配置可能错误或失效，请检查")
        except KeyError:
            logger.error("pica 账号密码可能错误，请检查")

    async def login(self):
        """登录获取token"""
        url = self.base_url / "auth" / "sign-in"
        send = {"email": self.account, "password": self.password}
        ret = await self.request(url, send, "POST")
        self.headers["authorization"] = ret["data"]["token"]

    async def categories(self):
        """获取所有目录"""
        url = self.base_url / "categories"
        return [from_dict(data_class=Category, data=c) for c in (await self.request(url))["data"]["categories"]]

    async def search(self, keyword: str) -> list[Comic]:
        """关键词搜索"""
        url = self.base_url / "comics" / "advanced-search" % {"page": 1}
        param = {"categories": [], "keyword": keyword, "sort": "ua"}
        return [
            from_dict(data_class=Comic, data=comic)
            for q in range(1, 3)
            for comic in (await self.request(url % {"q": q}, param, "POST"))["data"]["comics"]["docs"]
            if comic["likesCount"] > 200
        ]

    async def rank(self, tt: Literal["H24", "D7", "D30"] = "H24") -> list[Comic]:
        """排行榜"""
        url = self.base_url / "comics" / "leaderboard" % {"ct": "VC", "tt": tt}
        return [from_dict(data_class=Comic, data=comic) for comic in (await self.request(url))["data"]["comics"]]

    async def random(self) -> list[Comic]:
        """随机本子"""
        url = self.base_url / "comics" / "random"
        return [from_dict(data_class=Comic, data=comic) for comic in (await self.request(url))["data"]["comics"]]

    async def get_comic_from_id(self, _id: str) -> Comic | None:
        data = (await self.request(self.base_url / "comics" / _id))["data"]["comic"]
        comic = from_dict(data_class=Comic, data=data)
        comic.info = from_dict(data_class=ComicInfo, data=data)
        return comic


pica = Pica(username, password)
