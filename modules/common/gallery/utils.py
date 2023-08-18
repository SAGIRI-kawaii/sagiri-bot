import re
import random
import aiohttp
import hashlib
from pathlib import Path
from loguru import logger
from typing import Mapping, Literal

from creart import it
from kayaku import create
from avilla.core import Picture, Selector
from avilla.core.resource import RawResource, LocalFileResource

from shared.utils.control import Permission
from shared.models.config import GlobalConfig
from shared.utils.image import get_image_type, get_md5
from .models import GalleryConfig, GalleryInterval, GallerySwitch

json_pattern = r"json:([\w\W]+\.)+([\w\W]+)\$"
url_pattern = r"((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"


def random_pic(base_path: Path | str) -> Path:
    base_path = Path(base_path)
    path_dir = list(base_path.glob("*"))
    return random.sample(path_dir, 1)[0]


def cache_pic(cache_path: Path, raw: bytes):
    img_type = get_image_type(raw)
    if img_type != "Unknown":
        save_path = cache_path / f"{get_md5(raw)}.{img_type.lower()}"
        save_path.write_bytes(raw)
        logger.success(f"图片已缓存至{save_path.as_posix()}")


async def get_image(name: str, config: GalleryConfig) -> Picture | str:
    path = config.path
    proxy = create(GlobalConfig).proxy
    proxy = proxy if config.need_proxy else ""
    cache = config.cache
    if cache:
        cache_path = gen_cache_path(name, config)
    if re.match(json_pattern + url_pattern, path):
        json_paths = path.split("$")[0].split(":")[1].split(".")
        url = path.split("$")[1]
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(url, proxy=proxy) as resp:
                res = await resp.json(content_type=resp.content_type)
            for jp in json_paths:
                try:
                    res = res[int(jp[1:])] if jp[0] == "|" and jp[1:].isnumeric() else res.get(jp)
                except TypeError:
                    logger.error(f"图库<{name}>json解析失败！请查看配置路径是否正确或API是否有变动！配置：{path}")
                    return "json解析失败！请查看配置路径是否正确或API是否有变动！"
            async with session.get(res, proxy=proxy) as resp:
                raw = await resp.read()
                if cache:
                    cache_pic(cache_path, raw)
                return Picture(RawResource(raw))
    elif re.match(url_pattern, path):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(path, proxy=proxy) as resp:
                raw = await resp.read()
                if cache:
                    cache_pic(cache_path, raw)
                return Picture(RawResource(raw))
    elif Path(path).exists():
        return Picture(LocalFileResource(random_pic(path)))
    return Picture(LocalFileResource(Path.cwd() / "resources" / "error" / "path_not_exists.png"))


async def valid2send(scene: Selector | Mapping[str, str], gallery_name: str) -> bool | Literal["PermissionError", "IntervalError", "GalleryClosed"]:
    interval = it(GalleryInterval)
    g_data = create(GalleryConfig)[gallery_name]
    if interval.valid2send(scene, gallery_name):
        if (await Permission.get(scene)) >= g_data.privilege:
            if create(GallerySwitch).is_on(scene, gallery_name):
                interval.renew_time(scene, gallery_name)
                return True
            return "GalleryClosed"
        return "PermissionError"
    return "IntervalError"


def gen_cache_path(gallery: str, config: GalleryConfig) -> Path:
    base_path = Path(config.path)
    if not base_path.exists():
        if config.cache_path:
            base_path = Path(config.cache_path)
            if not base_path.exists():
                try:
                    base_path.mkdir(parents=True, exist_ok=True)
                    logger.success(f"自动创建图库{gallery}缓存文件夹（{base_path.absolute().as_posix()}）")
                except OSError:
                    logger.error(f"自动创建图库{gallery}缓存文件夹失败，尝试更改为默认位置")
    if not base_path.exists():
        base_path = Path.cwd() / "resources" / "cache" / gallery
        if not base_path.exists():
            base_path.mkdir(parents=True, exist_ok=True)
            logger.success(f"自动创建图库{gallery}缓存文件夹（{base_path.absolute().as_posix()}）")
    return base_path
