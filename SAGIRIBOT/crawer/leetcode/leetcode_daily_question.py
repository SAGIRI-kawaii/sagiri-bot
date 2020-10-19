import aiohttp

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain


async def get_leetcode_daily_question() -> list:
    """
    Get leetcode daily question

    :return:
    """
    api_url = "http://api.sagiri-web.com/leetcodeDailyQuestion/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=api_url) as resp:
            data = await resp.json()

    return [
        "None",
        MessageChain.create([
            Plain(text="".join(data["data"]))
        ])
    ]