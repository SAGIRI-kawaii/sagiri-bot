import os
import hmac
import time
import json
import uuid
import shutil
import aiohttp
import zipfile
import asyncio
import pyzipper
from io import BytesIO
from pathlib import Path
from urllib import parse
from loguru import logger
from hashlib import sha256
from PIL import Image as IMG
from aiohttp import TCPConnector
from typing import Literal, Optional, Tuple, Union

from creart import create

from sagiri_bot.config import GlobalConfig

BASE_PATH = os.path.dirname(__file__)
CACHE_PATH = f"{BASE_PATH}/cache/download"
global_url = "https://picaapi.picacomic.com/"
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
pica_config = config.functions.get("pica")
username = pica_config.get("username", None)
password = pica_config.get("password", None)
compress_password = pica_config.get("compress_password", "i_luv_sagiri")
DOWNLOAD_CACHE = pica_config.get("download_cache", True)


class Pica:
    def __init__(self, account, pwd):
        if not os.path.exists(CACHE_PATH):
            os.makedirs(CACHE_PATH)
        self.init = False
        self.account = account
        self.password = pwd
        self.header = header.copy()
        self.header["nonce"] = uuid_s
        asyncio.run_coroutine_threadsafe(self.check(), loop)

    @logger.catch
    async def check(self) -> bool:
        try:
            token = await self.login()
            self.header["authorization"] = token
            self.init = True
            return True
        except aiohttp.ClientConnectorError:
            logger.error("proxy配置可能错误或失效，请检查")
        except KeyError:
            logger.error("pica 账号密码可能错误，请检查")

    def update_signature(self, url: str, method: Literal["GET", "POST"]) -> dict:
        ts = str(int(time.time()))
        temp_header = self.header.copy()
        temp_header["time"] = ts
        temp_header["signature"] = self.encrypt(url, ts, method)
        if method == "GET":
            temp_header.pop("Content-Type")
        return temp_header

    @staticmethod
    def encrypt(url, ts, method):
        datas = [
            global_url,
            url.replace(global_url, ""),
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
        return (
            str(datas[1])
            + str(datas[2])
            + str(datas[3])
            + str(datas[4])
            + str(datas[5])
        )

    @staticmethod
    def __SigFromNative():
        return "~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn"

    @staticmethod
    def HashKey(src, key):
        app_secret = key.encode("utf-8")  # 秘钥
        data = src.lower().encode("utf-8")  # 数据
        return hmac.new(app_secret, data, digestmod=sha256).hexdigest()

    async def login(self):
        """登录获取token"""
        api = "auth/sign-in"
        url = global_url + api
        send = {"email": self.account, "password": self.password}
        temp_header = self.update_signature(url, "POST")
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.post(
                url=url, headers=temp_header, data=json.dumps(send), proxy=proxy
            ) as resp:
                self.header["authorization"] = (await resp.json())["data"]["token"]
        return self.header["authorization"]

    async def categories(self):
        """获取所有目录"""
        api = "categories"
        url = global_url + api
        temp_header = self.update_signature(url, "GET")
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(url=url, headers=temp_header, proxy=proxy) as resp:
                return (await resp.json())["data"]["categories"]

    async def search(self, keyword: str):
        """关键词搜索"""
        api = (
            global_url
            + "comics/search?page={0}"
            + "&q={0}".format(parse.quote(keyword))
        )
        url = api.format(1)
        # temp_header = self.update_signature(url, "GET")
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            # async with session.get(url=url, headers=temp_header, proxy=proxy) as resp:
            #     __pages = (await resp.json())["data"]["comics"]["pages"]
            _return = []
            for _ in range(1, 3):
                url = api.format(_)
                temp_header = self.update_signature(url, "GET")
                async with session.get(
                    url=url, headers=temp_header, proxy=proxy
                ) as resp:
                    __res = (await resp.json())["data"]["comics"]["docs"]
                    for __ in __res:
                        if __["likesCount"] < 200:
                            continue
                        if (
                            __["pagesCount"] / __["epsCount"] > 60
                            or __["epsCount"] > 10
                        ):
                            continue
                        _return.append({"name": __["title"], "id": __["_id"]})
        return _return

    async def random(self):
        """随机本子"""
        url = f"{global_url}comics/random"
        temp_header = self.update_signature(url, "GET")
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(url=url, headers=temp_header, proxy=proxy) as resp:
                return (await resp.json())["data"]["comics"]

    async def rank(self, tt: Literal["H24", "D7", "D30"] = "H24"):
        """排行榜"""
        url = f"{global_url}comics/leaderboard?ct=VC&tt={tt}"
        temp_header = self.update_signature(url, "GET")
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(url=url, headers=temp_header, proxy=proxy) as resp:
                return (await resp.json())["data"]["comics"]

    async def comic_info(self, book_id: str):
        """漫画详情"""
        url = f"{global_url}comics/{book_id}"
        temp_header = self.update_signature(url, "GET")
        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            async with session.get(url=url, headers=temp_header, proxy=proxy) as resp:
                return (await resp.json())["data"]["comic"]

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
                    IMG.open(BytesIO(image_bytes)).save(str(path))
                return image_bytes

    async def download_comic(
        self, book_id: str, return_zip: bool = True
    ) -> Optional[Tuple[str, Union[str, bytes]]]:
        info = await self.comic_info(book_id)
        episodes = info["epsCount"]
        comic_name = f"{info['title']} - {info['author']}"
        tasks = []
        for char in path_filter:
            comic_name = comic_name.replace(char, " ")
        comic_path = f"{CACHE_PATH}/{comic_name}"
        if not os.path.exists(comic_path):
            os.mkdir(comic_path)
        for episode in range(episodes):
            url = f"{global_url}comics/{book_id}/order/{episode + 1}/pages"
            temp_header = self.update_signature(url, "GET")
            async with aiohttp.ClientSession(
                connector=TCPConnector(ssl=False)
            ) as session:
                async with session.get(
                    url=url, headers=temp_header, proxy=proxy
                ) as resp:
                    data = (await resp.json())["data"]
            episode_title = data["ep"]["title"]
            episode_path = f"{comic_path}/{episode_title}"
            if not os.path.exists(episode_path):
                os.mkdir(episode_path)
            for img in data["pages"]["docs"]:
                media = img["media"]
                img_url = f"{media['fileServer']}/static/{media['path']}"
                image_path = f"{episode_path}/{media['originalName']}"
                print(comic_name, episode_title, media["originalName"], sep=" - ")
                if os.path.exists(image_path):
                    continue
                # _ = await self.download_image(img_url, image_path)
                tasks.append(
                    asyncio.create_task((self.download_image(img_url, image_path)))
                )
        _ = await asyncio.gather(*tasks)
        if return_zip:
            return self.zip_directory(comic_path, comic_name, compress_password)
        else:
            return comic_path, comic_name

    @staticmethod
    def zip_file(
        path: str, zip_name: str, pwd: str = "i_luv_sagiri"
    ) -> Optional[Tuple[str, bytes]]:
        shutil.make_archive(f"{path}/{zip_name}", "zip", path)
        with open(f"{path}/{zip_name}_密码{pwd}.zip", "rb") as r:
            return zip_name, r.read()

    @staticmethod
    def zip_directory(
        path, zip_name, pwd: str = "i_luv_sagiri"
    ) -> Optional[Tuple[str, bytes]]:
        if not os.path.exists(f"{path}/{zip_name}_密码{pwd}.zip"):
            if not os.path.exists(f"{path}/{zip_name}.zip"):
                with zipfile.ZipFile(Path(path) / f"{zip_name}.zip", mode="w") as zip_w:
                    len_dir_path = len(path)
                    for root, _, files in os.walk(path):
                        for file in files:
                            if file[-3:] == "zip":
                                continue
                            file_path = os.path.join(root, file)
                            zip_w.write(file_path, file_path[len_dir_path:])
            with pyzipper.AESZipFile(
                f"{path}/{zip_name}_密码{pwd}.zip",
                "w",
                compression=pyzipper.ZIP_LZMA,
                encryption=pyzipper.WZ_AES,
            ) as zf:
                zf.setpassword(pwd.encode())
                zf.setencryption(pyzipper.WZ_AES, nbits=128)
                zf.write(Path(path) / f"{zip_name}.zip", f"{zip_name}_密码{pwd}.zip")
        with open(f"{path}/{zip_name}_密码{pwd}.zip", "rb") as r:
            return f"{zip_name}_密码{pwd}", r.read()


pica = Pica(username, password)
# print(loop.run_until_complete(pica.search("SAGIRI")))
# print(loop.run_until_complete(pica.categories()))
# print(loop.run_until_complete(pica.random()))
# print(loop.run_until_complete(pica.rank()))
# print(loop.run_until_complete(pica.comic_info("5ce4d819431b5d017ddc8199")))
# loop.run_until_complete(pica.download_comic("5821a1d55f6b9a4f93ef4a6b"))
