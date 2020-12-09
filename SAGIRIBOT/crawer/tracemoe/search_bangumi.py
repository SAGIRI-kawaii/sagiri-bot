import base64
import aiohttp
from urllib.parse import quote

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.data_manage.update_data.set_get_image_ready import set_get_img_ready


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
                    Plain(text=f"name: {title_origin}\n"),
                    Plain(text=f"Chinese name: {title_chinese}\n"),
                    Plain(text=f"file name: {file_name}\n"),
                    Plain(text=f"time: {time_from}s ~ {time_to}s\n"),
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