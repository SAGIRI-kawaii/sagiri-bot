import aiohttp

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain


async def get_history_today() -> list:
    """
    Get history today

    Args:
        None

    Examples:
        message = await get_history_today()

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    api_url = "https://api.sagiri-web.com/historyToday/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=api_url) as resp:
            text = await resp.text()

    text = text.replace("\\n","\n")
    text = text[1:-1]
    while len(text) > 400:
        text = "\n".join(text.split("\n")[int(len(text.split("\n"))/2):])
    return [
        "None",
        MessageChain.create([
            Plain(text=text)
        ])
    ]