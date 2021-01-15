from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Plain

from third_party_library.MakiseVon.bookRcmd.bookRcmd import getImagePath


async def get_book_recommand_by_tag(tag: str) -> list:
    path = await getImagePath(tag)
    if path:
        return [
            "quoteSource",
            MessageChain.create([
                Image.fromLocalFile(path)
            ])
        ]
    else:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=f"没有找到有关{tag}的图书呐~换个标签吧~")
            ])
        ]