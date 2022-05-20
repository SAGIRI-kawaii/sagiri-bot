import functools

from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain


async def get_thumb(url: str, proxy: str) -> bytes:
    async with get_running(Adapter).session.get(url, proxy=proxy) as resp:
        return await resp.read()


def error_catcher(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return MessageChain(f"{func.__name__}运行出错：{str(e)}")
    return wrapper
