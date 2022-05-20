from typing import Optional, BinaryIO
from PicImageSearch import Network, EHentai

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain

from .utils import get_thumb, error_catcher


@error_catcher
async def ehentai_search(
    proxies: Optional[str] = None,
    cookies: Optional[str] = None,
    ex: bool = False, *,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should offer url or file!")
    if ex and not cookies:
        raise ValueError("If you use EXHentai Searcher, you should offer cookies!")
    async with Network(proxies=proxies, cookies=cookies) as client:
        ehentai = EHentai(client=client)
        if url:
            resp = await ehentai.search(url=url, ex=ex)
        elif file:
            resp = await ehentai.search(file=file, ex=ex)
        if not resp.raw:
            return MessageChain("EHentai未搜索到结果！")
        resp = resp.raw[0]
        return MessageChain([
            Plain("EHentai搜索到以下结果：\n"),
            Image(data_bytes=await get_thumb(resp.thumbnail, proxies)),
            Plain(f"\n标题：{resp.title}\n"),
            Plain(f"类别：{resp.type}\n"),
            Plain(f"上传日期：{resp.date}\n"),
            Plain(f"标签：{', '.join(resp.tags)}\n"),
            Plain(f"链接：{resp.url}")
        ])
