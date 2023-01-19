import hmac
import time
import asyncio
import aiohttp
import json
from yarl import URL
from enum import Enum
from os import PathLike
from pathlib import Path
from loguru import logger
from hashlib import sha256
from dacite import from_dict
from aiohttp import TCPConnector
from typing import Literal, TypeVar
from dataclasses import dataclass, field

from creart import create

from core import Sagiri

proxy = create(Sagiri).config.get_proxy()

T = TypeVar("T")


class ResponseType(Enum):
    JSON = dict
    BYTES = bytes
    TEXT = str


class PicaMethod:
    api_key: str = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
    nonce: str = "b1ab87b4800d4d4590a11701b8551afa"
    secret_key: str = r"~d}$Q7$eIni=V)9\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn"
    base_url: URL = URL("https://picaapi.picacomic.com/")
    headers: dict = {
        "api-key": "C69BAF41DA5ABD1FFEDC6D2FEA56B",
        "accept": "application/vnd.picacomic.com.v1+json",
        "app-channel": "2",
        "nonce": "b1ab87b4800d4d4590a11701b8551afa",
        "app-version": "2.2.1.2.3.3",
        "app-uuid": "defaultUuid",
        "app-platform": "android",
        "app-build-version": "44",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "okhttp/3.8.1",
        "image-quality": "original",
    }
    account: str
    password: str
    proxy: str | None
    session: aiohttp.ClientSession
    loop: asyncio.AbstractEventLoop

    def __init__(self, session: aiohttp.ClientSession | None = None):
        self.proxy = proxy
        self.loop = create(asyncio.AbstractEventLoop)
        self.session = session or aiohttp.ClientSession(
            connector=TCPConnector(ssl=False)
        )

    def __del__(self):
        asyncio.run_coroutine_threadsafe(self.session.close(), self.loop)

    async def request(
        self,
        url: str | URL,
        params: dict[str, str] | None = None,
        method: Literal["GET", "POST"] = "GET",
        return_type: type[T] = dict,
    ) -> T:
        temp_header = self.update_signature(url, method)
        data = json.dumps(params) if params else None
        async with self.session.request(
            method, url=url, headers=temp_header, proxy=self.proxy, data=data
        ) as resp:
            ret_data = await resp.json()
            if not resp.ok:
                logger.warning(f"报错返回json: {ret_data}")

            if return_type is dict:
                return await resp.json()
            elif return_type is bytes:
                return await resp.read()
            elif return_type is str:
                return await resp.text(encoding="utf-8")
            else:
                raise ValueError("Unsupported return type")

    @staticmethod
    def update_signature(url: str | URL, method: Literal["GET", "POST"]) -> dict:
        if isinstance(url, str):
            url = URL(url)
        ts = str(int(time.time()))
        temp_header = PicaMethod.headers.copy()
        temp_header["time"] = ts
        temp_header["signature"] = PicaMethod.encrypt(url, ts, method)
        if method == "GET":
            temp_header.pop("Content-Type")
        return temp_header

    @staticmethod
    def encrypt(url: URL, ts, method):
        datas = [
            PicaMethod.base_url,
            url.path_qs[1:],
            ts,
            PicaMethod.nonce,
            method,
            "C69BAF41DA5ABD1FFEDC6D2FEA56B",
            "2.2.1.3.3.4",
            "45",
        ]
        src = PicaMethod.__con_from_native(datas)
        key = PicaMethod.secret_key
        return PicaMethod.hash_key(src, key)

    @staticmethod
    def __con_from_native(datas):
        return "".join(map(str, datas[1:6]))

    @staticmethod
    def hash_key(src, key):
        app_secret = key.encode("utf-8")  # 秘钥
        data = src.lower().encode("utf-8")  # 数据
        return hmac.new(app_secret, data, digestmod=sha256).hexdigest()


@dataclass
class Image:
    """图片"""

    originalName: str = field(default_factory=str)
    path: str = field(default_factory=str)
    fileServer: str = field(default_factory=str)

    async def get(
        self,
        *,
        folder: str | PathLike | None = None,
        file_name: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> bytes:
        if not self.path or not self.fileServer:
            raise ValueError("Missing necessary parameter path or fileServer!")

        if folder is not None:
            folder = Path(folder)
            folder.mkdir(parents=True, exist_ok=True)
            file_path = folder / (file_name or self.originalName)
            if file_path.exists():
                return file_path.read_bytes()

        init_session = not bool(session)
        session = session or aiohttp.ClientSession(connector=TCPConnector(ssl=False))
        url = URL(self.fileServer) / "static" / self.path
        async with session.get(
            url, headers=PicaMethod.update_signature(url, "GET"), proxy=proxy
        ) as resp:
            image_bytes = await resp.read()
            if folder is not None:
                (folder / (file_name or self.originalName)).write_bytes(image_bytes)
        if init_session:
            await session.close()
        return image_bytes


@dataclass
class Creator:
    """漫画上传者"""

    _id: str = field(default_factory=str)
    gender: str = field(default_factory=str)
    name: str = field(default_factory=str)
    verified: bool = field(default_factory=bool)
    exp: int = field(default_factory=int)
    level: int = field(default_factory=int)
    role: str = field(default_factory=str)
    characters: list[str] = field(default_factory=list)
    avatar: Image = field(default_factory=Image)
    title: str = field(default_factory=str)
    slogan: str = field(default_factory=str)


@dataclass
class Category:
    """板块分类"""

    _id: str = field(default_factory=str)
    title: str = field(default_factory=str)
    description: str = field(default_factory=str)
    thumb: Image = field(default_factory=Image)
    isWeb: bool = field(default=False)
    active: bool = field(default=False)
    link: str = field(default_factory=str)


@dataclass
class Episode:
    """漫画章节"""

    docs: list[Image] = field(default_factory=list)
    total: int = field(default_factory=int)
    limit: int = field(default_factory=int)
    page: int = field(default_factory=int)
    pages: int = field(default_factory=int)
    _id: str = field(default_factory=str)
    title: str = field(default_factory=str)

    async def download(
        self,
        *,
        folder: str | PathLike | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> list[bytes]:
        return await asyncio.gather(
            *[i.get(folder=folder, session=session) for i in self.docs]
        )


@dataclass
class Comic(PicaMethod):
    """漫画基本信息"""

    updated_at: str = field(default_factory=str)
    thumb: Image = field(default_factory=Image)
    author: str = field(default_factory=str)
    description: str = field(default_factory=str)
    chineseTeam: str = field(default_factory=str)
    created_at: str = field(default_factory=str)
    finished: bool = field(default_factory=bool)
    totalViews: int = field(default_factory=int)
    categories: list[str] = field(default_factory=list)
    totalLikes: int = field(default_factory=int)
    title: str = field(default_factory=str)
    tags: list[str] = field(default_factory=list)
    _id: str = field(default_factory=str)
    likesCount: int = field(default_factory=int)
    episodes: list[Episode] = field(default_factory=list)
    info: "ComicInfo" = None

    def __post_init__(self):
        super().__init__()

    def __del__(self):
        asyncio.run_coroutine_threadsafe(self.session.close(), self.loop)

    @property
    def id(self):
        return self._id

    @property
    def likes(self):
        return self.likesCount

    async def get_info(self) -> "ComicInfo":
        if self.info:
            return self.info
        self.info = from_dict(
            data_class=ComicInfo,
            data=(await self.request(self.base_url / "comics" / self._id))["data"][
                "comic"
            ],
        )
        return self.info

    async def get_episodes(self) -> list[Episode]:
        if self.episodes:
            return self.episodes
        info = await self.get_info()
        for episode in range(info.epsCount):
            episode_end = False
            episode_data = {
                "docs": [],
                "total": 0,
                "limit": 0,
                "page": 1,
                "pages": 0,
                "_id": "",
                "title": "",
            }
            while not episode_end:
                url = (
                    self.base_url
                    / "comics"
                    / self._id
                    / "order"
                    / str(episode + 1)
                    / "pages"
                    % {"page": episode_data["page"] + 1}
                )
                data: dict = (await self.request(url))["data"]
                data.update(data["pages"])
                data.update(data["ep"])
                del data["ep"]
                episode_data["docs"].extend(data["docs"])
                episode_data["total"] = data["total"]
                episode_data["limit"] = data["limit"]
                episode_data["page"] = data["page"]
                episode_data["pages"] = data["pages"]
                episode_data["_id"] = data["_id"]
                episode_data["title"] = data["title"]
                for docs in data["docs"]:
                    docs.update(docs["media"])
                    del docs["media"]
                if data["page"] == data["pages"]:
                    episode_end = True
            self.episodes.append(from_dict(data_class=Episode, data=episode_data))
        return self.episodes

    async def download(self, folder: Path) -> list[list[bytes]]:
        episodes = await self.get_episodes()
        # for i in episodes: print(len(i.docs))
        return await asyncio.gather(
            *[
                episode.download(folder=folder / episode.title, session=self.session)
                for episode in episodes
            ]
        )


@dataclass
class ComicInfo(Comic):
    """漫画详情"""

    _creator: Creator = field(default_factory=Creator)
    pagesCount: int = field(default_factory=int)
    epsCount: int = field(default_factory=int)
    allowDownload: bool = field(default=True)
    allowComment: bool = field(default=True)
    totalComments: int = field(default_factory=int)
    viewsCount: int = field(default_factory=int)
    commentsCount: int = field(default_factory=int)
    isFavourite: bool = field(default=False)
    isLiked: bool = field(default=False)


class Order(Enum):
    DEFAULT = "ua"  # 默认
    LATEST = "dd"  # 新到旧
    OLDEST = "da"  # 旧到新
    LOVED = "ld"  # 最多爱心
    POINT = "vd"  # 最多指名
