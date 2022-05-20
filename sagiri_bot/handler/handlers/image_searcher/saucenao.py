from typing import Optional, BinaryIO
from PicImageSearch import Network, SauceNAO

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain

from .utils import get_thumb, error_catcher


@error_catcher
async def saucenao_search(
    api_key: str, proxies: Optional[str] = None, *,
    url: Optional[str] = None,
    file: Optional[BinaryIO] = None
) -> MessageChain:
    if not url and not file:
        raise ValueError("You should give url or file!")
    if not api_key:
        return MessageChain("未配置SAUCENAO_API_KEY!")
    async with Network(proxies=proxies) as client:
        saucenao = SauceNAO(client=client, api_key=api_key)
        if url:
            resp = await saucenao.search(url=url)
        elif file:
            resp = await saucenao.search(file=file)
        if not resp.raw:
            return MessageChain("SAUCENAO未搜索到结果！")
        resp = resp.raw[0]
        return MessageChain([
            Plain("SAUCENAO搜索到以下结果：\n"),
            Image(data_bytes=await get_thumb(resp.thumbnail, proxies)),
            Plain(f"\n标题：{resp.title}\n"),
            Plain(f"相似度：{resp.similarity}%\n"),
            Plain(f"作者：{resp.author}\n"),
            Plain(f"pixiv图像 id：{resp.pixiv_id}\n" if resp.pixiv_id else ''),
            Plain(f"pixiv画师 id：{resp.member_id}\n" if resp.member_id else ''),
            Plain(f"链接：{resp.url}")
        ])
