import aiohttp
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain


async def get_jlu_csw_notice() -> list:
    """
    Get JLU CSW notice

    Args:
        None

    Examples:
        msg = await get_jlu_csw_notice()

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    url = "http://api.sagiri-web.com/JLUCSWNotice/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            res = await resp.json()

    data = res["data"]
    content = "----------------------------------\n"
    for i in range(5):
        content += f"{data[i]['title']}\n"
        content += f"{data[i]['href']}\n"
        content += f"                                        {data[i]['time'].replace('-', '.')}\n"
        content += "----------------------------------\n"
    return [
        "None",
        MessageChain.create([
            Plain(text=content)
        ])
    ]
