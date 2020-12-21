import aiohttp
import asyncio
from PIL import Image as IMG
from io import BytesIO
import os
from urllib.parse import quote

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.get_config import get_config


async def get_setu_keyword(keyword: str) -> list:
    """
    Search image by keyword

    Args:
        keyword: Keyword to search

    Examples:
        msg = await get_setu_keyword(keyword)

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    url = f"https://api.sagiri-web.com/setu/?keyword={quote(keyword)}"
    # print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            res = await resp.json()
    print(res)
    count = res["result count"]
    if count == 0:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="没有找到呢~可能还没有收录呢~也可能是你的XP系统太怪了叭（")
            ])
        ]

    data = res["data"][0]
    img_url = data["url"]
    # print(img_url)

    save_base_path = await get_config("setuPath")
    path = save_base_path + f"{data['pid']}_p{data['p']}.png"

    if not os.path.exists(path):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=img_url) as resp:
                img_content = await resp.read()

        image = IMG.open(BytesIO(img_content))
        image.save(path)

    return [
        "quoteSource",
        MessageChain.create([
            Plain(text=f"你要的{keyword}涩图来辣！\n"),
            Image.fromLocalFile(path),
            Plain(text=f"title:{data['title']}"),
            Plain(text=f"\nurl:{data['url']}\n")
        ])
    ]


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # Blocking call which returns when the display_date() coroutine is done
    res = loop.run_until_complete(get_setu_keyword("刀剑神域"))
    print(res)
    loop.stop()
    loop.close()
