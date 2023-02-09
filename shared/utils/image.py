import aiohttp
from yarl import URL

from graia.ariadne.event.message import Friend, Member


async def get_image(url: URL | str, proxy: str = "") -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy) as resp:
            return await resp.read()


async def get_user_avatar(user: Friend | Member | int | str, size: int = 640) -> bytes:
    if isinstance(user, Friend | Member):
        user = user.id
    if isinstance(user, str) and not user.isnumeric():
        raise ValueError
    url = f"https://q1.qlogo.cn/g?b=qq&nk={user}&s={size}"
    return await get_image(url)
