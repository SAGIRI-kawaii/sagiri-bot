import aiohttp
import os
from PIL import Image as IMG
from io import BytesIO
import urllib.parse as parse

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.basics.tools import messagechain_to_img


async def get_bangumi_info(sender: int, keyword: str) -> list:
    headers = {
        "user-agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
    }
    url = "https://api.bgm.tv/search/subject/%s?type=2&responseGroup=Large&max_results=1" % parse.quote(keyword)
    print(url)
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers) as resp:
            data = await resp.json()

    if "code" in data.keys() and data["code"] == 404:
        return [
            "None",
            MessageChain.create([
                At(target=sender),
                Plain(text="番剧 %s 未搜索到结果！" % keyword)
            ])
        ]
    print(data)
    bangumi_id = data["list"][0]["id"]
    url = "https://api.bgm.tv/subject/%s?responseGroup=medium" % bangumi_id
    print(url)

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers) as resp:
            data = await resp.json()

    name = data["name"]
    cn_name = data["name_cn"]
    summary = data["summary"]
    img_url = data["images"]["large"]
    score = data["rating"]["score"]
    rank = data["rank"]
    rating_total = data["rating"]["total"]
    save_base_path = await get_config("imgSavePath")
    path = save_base_path + "%s.jpg" % name

    if not os.path.exists(path):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=img_url) as resp:
                img_content = await resp.read()
        image = IMG.open(BytesIO(img_content))
        image.save(path)
    message = MessageChain.create([
            Plain(text="查询到以下信息：\n"),
            Image.fromLocalFile(path),
            Plain(text="名字:%s\n\n中文名字:%s\n\n" % (name, cn_name)),
            Plain(text="简介:%s\n\n" % summary),
            Plain(text="bangumi评分:%s(参与评分%s人)\n\n" % (score, rating_total)),
            Plain(text="bangumi排名:%s" % rank)
        ])
    return [
        "quoteSource",
        await messagechain_to_img(message=message, max_width=1080, img_fixed=True)
    ]
