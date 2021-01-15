from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.bot_status.get_file_count import get_file_count


async def get_bot_status(base_name: str, group_id: int) -> list:
    legal_status_name = {"all", "memory", "system", "cpu", "setting", "bot"}
    legal_gallery_name = {"setu", "setu18", "real", "realHighq", "bizhi"}
    if base_name in legal_gallery_name:
        return [
            "None",
            MessageChain.create([
                Plain(text=f"{base_name}图库总数量：{await get_file_count(base_name)}")
            ])
        ]
    elif base_name in legal_status_name:
        return [
            "None",
            Plain(text="SAGIRI-BOT STATUS:")
        ]
    else:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="base_name错误！")
            ])
        ]
