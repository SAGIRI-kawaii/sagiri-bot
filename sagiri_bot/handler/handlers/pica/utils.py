import zipfile
from pathlib import Path
from typing import Optional

import pyzipper
from creart import create
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from sagiri_bot.config import GlobalConfig
from utils.text_engine.adapter import GraiaAdapter
from utils.text_engine.text_engine import TextEngine

from .Pica import pica

config = create(GlobalConfig)
DOWNLOAD_CACHE = config.functions["pica"]["download_cache"]
SEARCH_CACHE = config.functions["pica"]["search_cache"]

BASE_PATH = Path(__file__).parent
SEARCH_CACHE_PATH = BASE_PATH / "cache" / "search"


async def pica_t2i(comic_info, is_search: bool = False, rank: Optional[int] = None):
    return Image(
        data_bytes=TextEngine(
            [
                GraiaAdapter(
                    MessageChain(
                        [
                            await get_thumb(comic_info),
                            f"\n排名：{rank}\n" if rank is not None else "",
                            f"\n名称：{comic_info['title']}\n"
                            f"作者：{comic_info['author']}\n"
                            f"描述：{comic_info['description']}\n"
                            if is_search
                            else "",
                            f"分类：{'、'.join(comic_info['categories'])}\n"
                            f"标签：{'、'.join(comic_info['tags'])}\n"
                            if is_search
                            else "",
                            f"页数：{comic_info['pagesCount']}\n"
                            f"章节数：{comic_info['epsCount']}\n"
                            f"完结状态：{'已完结' if comic_info['finished'] else '未完结'}\n"
                            f"喜欢: {comic_info['totalLikes']}    "
                            f"浏览次数: {comic_info['totalViews']}    ",
                        ]
                    )
                )
            ],
            max_width=2160,
        ).draw()
    )


def zip_directory(path: Path, zip_name, pwd: str = "i_luv_sagiri") -> Path:
    zip_file = path.parent / f"{zip_name}.zip"
    encrypt_zip_file = path.parent / f"{zip_name}_密码{pwd}.zip"
    with zipfile.ZipFile(zip_file, mode="w") as zip_w:
        for entry in path.rglob("*"):
            zip_w.write(entry, entry.relative_to(path))

    with pyzipper.AESZipFile(
        encrypt_zip_file,
        "w",
        compression=pyzipper.ZIP_LZMA,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(pwd.encode())
        zf.setencryption(pyzipper.WZ_AES, nbits=128)
        zf.write(zip_file, encrypt_zip_file.name)

    zip_file.unlink()
    return encrypt_zip_file


async def get_thumb(comic_info: dict) -> Image:
    thumb = SEARCH_CACHE_PATH / f"{comic_info['_id']}.jpg"
    if thumb.exists():
        return Image(path=thumb)
    else:
        return Image(
            data_bytes=await pica.download_image(
                url=f"{comic_info['thumb']['fileServer']}/static/{comic_info['thumb']['path']}",
                path=thumb if SEARCH_CACHE else None,
            )
        )
