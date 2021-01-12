import aiohttp
import json

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain


async def get_almanac() -> list:
    url = "https://www.free-api.com/urltask"
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        "Accept": "application / json, text / javascript, * / *; q = 0.01",
        "X-CSRF-TOKEN": "Wsztz9Ov40q9k1O3T1xEI6woy0uj8VlZN7I1AlGR"
    }
    payload = {
        "year": 2021,
        "month": 1,
        "day": 1
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=payload) as resp:
            data = await resp.read()
    print(data)
    return [
        "None",
        MessageChain.create([
            Plain(text=str(data))
        ])
    ]
    # print(tr)
