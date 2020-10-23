import os
import aiohttp
from PIL import Image as IMG
from io import BytesIO
import re

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.get_config import get_config


async def get_steam_game_description(game_id: int) -> str:
    """
    Return game description on steam

    Args:
        game_id: Steam shop id of target game

    Examples:
        get_steam_game_description(502010)

    Return:
        str
    """
    url = "https://store.steampowered.com/app/%s/" % game_id
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            html = await resp.text()
    description = re.findall(r'<div class="game_description_snippet">(.*?)</div>', html, re.S)
    if len(description) == 0:
        return "none"
    return description[0].lstrip().rstrip()


async def get_steam_game_search(keyword: str) -> list:
    """
    Return search result

    Args:
        keyword: Keyword to search(game name)

    Examples:
        get_steam_game_search("Monster Hunter")

    Return:
        [
            str,
            MessageChain
        ]
    """
    url = "https://steamstats.cn/api/steam/search?q=%s&page=1&format=json&lang=zh-hans" % keyword
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6",
        "pragma": "no-cache",
        "referer": "https://steamstats.cn/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as resp:
            result = await resp.json()

    if len(result["data"]["results"]) == 0:
        return [
            "AtSender",
            MessageChain.create([
                Plain(text="搜索不到%s呢~检查下有没有吧~偷偷告诉你，搜英文名的效果可能会更好哟~" % keyword)
            ])
        ]
    else:
        result = result["data"]["results"][0]
        base_path = await get_config("steamSearch")
        path = "%s%s.png" % (base_path, result["app_id"])
        print("cache:%s" % os.path.exists(path))
        if not os.path.exists(path):
            async with aiohttp.ClientSession() as session:
                async with session.get(url=result["avatar"]) as resp:
                    img_content = await resp.read()
            image = IMG.open(BytesIO(img_content))
            image.save(path)
        description = await get_steam_game_description(result["app_id"])
        return [
            "AtSender",
            MessageChain.create([
                Plain(text="\n搜索到以下信息：\n"),
                Plain(text="游戏：%s (%s)\n" % (result["name"], result["name_cn"])),
                Plain(text="游戏id：%s\n" % result["app_id"]),
                Image.fromLocalFile(path),
                Plain(text="游戏描述：%s\n" % description),
                Plain(text="\nsteamUrl:https://store.steampowered.com/app/%s/" % result["app_id"])
            ])
        ]
