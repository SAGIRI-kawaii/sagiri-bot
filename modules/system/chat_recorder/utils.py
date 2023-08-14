import re
import jieba
import asyncio

from avilla.core import Message
from graia.amnesia.message.chain import MessageChain

jieba.setLogLevel(jieba.logging.INFO)
pattern = re.compile(r"[^\w\s]")


async def seg_content(content: Message | MessageChain | str) -> str:
    if isinstance(content, Message):
        content = str(content.content)
    elif isinstance(content, MessageChain):
        content = str(content)
    seg = await asyncio.to_thread(jieba.cut, pattern.sub("", content))
    return "|".join(seg)