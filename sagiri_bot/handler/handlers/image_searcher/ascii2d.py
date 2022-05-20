from typing import Optional, BinaryIO
from PicImageSearch import Network, Ascii2D

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain

from .utils import get_thumb, error_catcher

bovw = True


@error_catcher
async def ascii2d_search(
    proxies: Optional[str] = None, *,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should offer url or file!")
    async with Network(proxies=proxies) as client:
        ascii2d = Ascii2D(client=client, bovw=bovw)
        if url:
            resp = await ascii2d.search(url=url)
        elif file:
            resp = await ascii2d.search(file=file)
        if not resp.raw:
            return MessageChain("ASCII2D未搜索到结果！")
        resp = resp.raw[1]
        return MessageChain([
            Plain("ASCII2D搜索到以下结果：\n"),
            Image(data_bytes=await get_thumb(resp.thumbnail, proxies)),
            Plain(f"\n标题：{resp.title}\n"),
            Plain(f"作者：{resp.author}\n"),
            Plain(f"图像详情：{resp.detail}\n"),
            Plain(f"链接：{resp.url}")
        ])
