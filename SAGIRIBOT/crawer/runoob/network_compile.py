import aiohttp


legal_language = {
    "R": 80,
    "vb": 84,
    "ts": 1001,
    "kt": 19,
    "pas": 18,
    "lua": 17,
    "node.js": 4,
    "go": 6,
    "swift": 16,
    "rs": 9,
    "sh": 11,
    "pl": 14,
    "erl": 12,
    "scala": 5,
    "cs": 10,
    "rb": 1,
    "cpp": 7,
    "c": 7,
    "java": 8,
    "py3": 15,
    "py": 0,
    "php": 3
}


async def network_compile(language: str, code: str):
    if language not in legal_language:
        return f"支持的语言：{', '.join(list(legal_language.keys()))}"
    url = "https://tool.runoob.com/compile2.php"
    payload = {
        "code": code,
        "token": "4381fe197827ec87cbac9552f14ec62a",
        "stdin": "",
        "language": legal_language[language],
        "fileext": language
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
