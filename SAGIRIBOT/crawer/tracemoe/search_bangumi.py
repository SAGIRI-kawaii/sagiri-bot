import base64
import aiohttp
from urllib.parse import quote
from PIL import Image as IMG
from io import BytesIO

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.data_manage.update_data.set_get_image_ready import set_get_img_ready


async def sec_to_str(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


async def search_bangumi(group_id: int, sender: int, img_url: str) -> list:

    await set_get_img_ready(group_id, sender, False, "searchBangumiReady")

    async with aiohttp.ClientSession() as session:
        async with session.get(url=img_url) as resp:
            img_content = await resp.read()

    url = "https://trace.moe/search"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    image_b64 = base64.b64encode(img_content)

    params = f"data={quote(f'data:image/jpeg;base64,{image_b64.decode()}')}&filter={''}&trial={'0'}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=params) as resp:
            result = await resp.json()

    docs = result["docs"]
    if docs:
        try:
            print(docs[0])
            title_chinese = docs[0]["title_chinese"]
            title_origin = docs[0]["title_chinese"]
            file_name = docs[0]["file"]
            anilist_id = docs[0]["anilist_id"]
            time_from = docs[0]["from"]
            time_to = docs[0]["to"]

            t = docs[0]["t"]
            tokenthumb = docs[0]["tokenthumb"]
            thumbnail_url = f"https://trace.moe/thumbnail.php?anilist_id={anilist_id}&file={quote(file_name)}&t={t}&token={tokenthumb}"
            print(thumbnail_url)
            # 下载缩略图
            path = "./statics/temp/tempSearchBangumi.jpg"
            async with aiohttp.ClientSession() as session:
                async with session.get(url=thumbnail_url) as resp:
                    thumbnail_content = await resp.read()
            image = IMG.open(BytesIO(thumbnail_content))
            image.save(path)

            url = f"https://trace.moe/info?anilist_id={anilist_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url) as resp:
                    result = await resp.json()
            result = result[0]
            start_date = f"{result['startDate']['year']}-{result['startDate']['month']}-{result['startDate']['day']}"
            end_date = f"{result['endDate']['year']}-{result['endDate']['month']}-{result['endDate']['day']}"
            score = result["averageScore"]
            return [
                "quoteSource",
                MessageChain.create([
                    Plain(text="搜索到结果：\n"),
                    Image.fromLocalFile(path),
                    Plain(text=f"name: {title_origin}\n"),
                    Plain(text=f"Chinese name: {title_chinese}\n"),
                    Plain(text=f"file name: {file_name}\n"),
                    Plain(text=f"time: {await sec_to_str(time_from)} ~ {await sec_to_str(time_to)}\n"),
                    Plain(text=f"score: {score}\n"),
                    Plain(text=f"Broadcast date: {start_date} ~ {end_date}\n")
                ])
            ]
        except Exception as e:
            return [
                "quoteSource",
                MessageChain.create([
                    Plain(text="出错了呢~\n"),
                    Plain(text=str(e))
                ])
            ]
    else:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="没有搜索到结果呐~")
            ])
        ]