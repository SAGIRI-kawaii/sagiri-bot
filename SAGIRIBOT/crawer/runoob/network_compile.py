import aiohttp


async def network_py3_compile(code: str):
    url = "https://tool.runoob.com/compile2.php"
    payload = {
        "code": code,
        "token": "4381fe197827ec87cbac9552f14ec62a",
        "stdin": "",
        "language": 15,
        "fileext": "py3"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=payload) as resp:
            res = await resp.json()
    return {
        "output": res["output"],
        "errors": res["errors"]
    }
