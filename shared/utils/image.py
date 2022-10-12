import aiohttp

from graia.ariadne.event.message import Friend, Member


async def get_user_avatar(user: Friend | Member | int | str) -> bytes:
    if isinstance(user, Friend | Member):
        user = user.id
    if isinstance(user, str) and not user.isnumeric():
        raise ValueError
    url = f"http://q1.qlogo.cn/g?b=qq&nk={user}&s=640"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()
