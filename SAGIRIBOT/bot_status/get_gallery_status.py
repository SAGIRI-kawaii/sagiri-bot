from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.bot_status.get_file_count import get_file_count


async def get_gallery_status(base_name: str) -> list:
    legal_name = {"setu", "setu18", "real", "realHighq", "bizhi"}
    if base_name not in legal_name:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="base_name错误！")
            ])
        ]
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text=f"{base_name}图库总数量：{await get_file_count(base_name)}")
            ])
        ]