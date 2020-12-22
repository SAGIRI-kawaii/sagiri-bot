import aiohttp
import json


async def get_proxy() -> dict:
    url = "http://ipproxy.sagiri-web.com/get/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            res = await resp.text()

    print(res)

    return json.loads(res)
