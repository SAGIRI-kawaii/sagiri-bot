import zipfile
from base64 import b64encode
from pathlib import Path

import pyzipper
from creart import create
from graia.ariadne.message.element import Image

from shared.models.config import GlobalConfig
from shared.utils.text2img import md2img

from .model import Comic, ComicInfo

config = create(GlobalConfig)
DOWNLOAD_CACHE = config.functions["pica"]["download_cache"]
SEARCH_CACHE = config.functions["pica"]["search_cache"]

BASE_PATH = Path(__file__).parent
SEARCH_CACHE_PATH = BASE_PATH / "cache" / "search"


async def pica_t2i(comic_info: ComicInfo | Comic, rank: int | None = None):
    # ComicInfo if is_search else Comic
    thumb = await comic_info.thumb.get()
    md = f"<img src='data:image/png;base64, {b64encode(thumb).decode()}'/><br>"
    if rank:
        md += f"排名：{rank}<br>"
    md += f"名称：{comic_info.title}<br>"
    md += f"作者：{comic_info.author}<br>"
    if isinstance(comic_info, ComicInfo):
        md += f"描述：{comic_info.description}<br>"
    md += f"分类：{'、'.join(comic_info.categories)}<br>"
    if isinstance(comic_info, ComicInfo):
        md += f"标签：{'、'.join(comic_info.tags)}<br>" if comic_info.tags else ""
    if isinstance(comic_info, ComicInfo):
        md += f"页数：{comic_info.pagesCount}<br>"
        md += f"章节数：{comic_info.epsCount}<br>"
    md += f"完结状态：{'已完结' if comic_info.finished else '未完结'}<br>"
    md += f"喜欢: {comic_info.totalLikes}<br>"
    md += f"浏览次数: {comic_info.totalViews}"
    return Image(data_bytes=await md2img(md))


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
