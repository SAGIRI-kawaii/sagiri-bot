from typing import TypedDict, Mapping

from creart import it
from avilla.core import Selector
from kayaku import config, create

from .gpt import GPT
from .preset import preset_dict
from shared.models.config import GlobalConfig
from shared.utils.models import selector2pattern

SceneType = Mapping[str, str] | Selector
proxy = create(GlobalConfig).proxy


@config("modules.gpt")
class GPTConfig:
    openai_key: str = ""
    host: str = "https://api.openai.com/v1/chat/completions"


class MemberGPT(TypedDict):
    running: bool
    gpt: GPT


class ConversationManager(object):
    def __init__(self):
        self.data: dict[int, dict[int, MemberGPT]] = {}

    async def new(self, sender: SceneType | str, preset: str = "", max_round: int = 1000):
        if not isinstance(sender, str):
            sender = selector2pattern(sender)
        preset = preset_dict[preset]["content"] \
            if preset in preset_dict else \
            (preset if preset else preset_dict["sagiri"]["content"])
        if sender in self.data:
            self.data[sender]["gpt"].reset(preset=preset, max_round=max_round)
        else:
            cfg = create(GPTConfig)
            self.data[sender] = {"running": False, "gpt": GPT(cfg.openai_key, preset, proxy, max_round, cfg.host)}

    async def send_message(
        self, sender: SceneType, content: str, custom_message: list = None, with_token: bool = True
    ) -> str:
        if not isinstance(sender, str):
            sender = selector2pattern(sender)
        if sender not in self.data:
            _ = await self.new(sender)
        if self.data[sender]["running"]:
            return "我上一句话还没结束呢，别急阿~等我回复你以后你再说下一句话喵~"
        self.data[sender]["running"] = True
        try:
            result = await self.data[sender]["gpt"].send_message(content, custom_message, with_token)
        except Exception as e:
            result = f"发生错误：{e}，请稍后再试"
        finally:
            self.data[sender]["running"] = False
        return result

    async def set_max_round(self, sender: SceneType | str, max_round: int = 1000):
        if not isinstance(sender, str):
            sender = selector2pattern(sender)
        if sender not in self.data :
            _ = await self.new(sender)
        self.data[sender]["gpt"].max_round = max_round


manager = ConversationManager()
