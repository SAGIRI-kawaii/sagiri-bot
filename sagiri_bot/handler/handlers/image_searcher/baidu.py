from typing import Optional, BinaryIO
from PicImageSearch import Network, BaiDu

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain

from .utils import get_thumb, error_catcher


@error_catcher
async def baidu_search(
    *,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should offer url or file!")
    async with Network() as client:
        baidu = BaiDu(client=client)
        if url:
            resp = await baidu.search(url=url)
        elif file:
            resp = await baidu.search(file=file)
        if not resp.raw:
            return MessageChain("BAIDU未搜索到结果！")
        resp = resp.raw[2]
        return MessageChain([
            Plain("BAIDU搜索到以下结果：\n"),
            Image(data_bytes=await get_thumb(resp.image_src, '')),
            Plain(f"\n标题：{resp.title}\n"),
            Plain(f"摘要：{resp.abstract}\n"),
            Plain(f"链接：{resp.url}")
        ])
