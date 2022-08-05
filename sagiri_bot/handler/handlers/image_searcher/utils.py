import aiohttp
import functools

from graia.ariadne.message.chain import MessageChain


async def get_thumb(url: str, proxy: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy) as resp:
            return await resp.read()


def error_catcher(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return MessageChain(f"{func.__name__}运行出错：{str(e)}")
    return wrapper
