from typing import TypedDict

from creart import create
from graia.ariadne.model.relationship import Group, Member

from core import Sagiri
from .gpt3_5 import GPT35
from .preset import preset_dict

config = create(Sagiri).config
proxy = config.get_proxy()
openai_key = config.functions.get("openai_key")


class MemberGPT(TypedDict):
    running: bool
    gpt: GPT35


class ConversationManager(object):
    def __init__(self):
        self.data: dict[int, dict[int, MemberGPT]] = {}

    async def new(self, group: Group | int, member: Member | int, preset: str = ""):
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        preset = preset_dict[preset]["content"] \
            if preset in preset_dict else \
            (preset if preset else preset_dict["sagiri"]["content"])
        if group in self.data:
            if member in self.data[group]:
                _ = self.data[group][member]["gpt"].reset(preset=preset)
            else:
                self.data[group][member] = {"running": False, "gpt": GPT35(openai_key, preset, proxy)}
        else:
            self.data[group] = {}
            self.data[group][member] = {"running": False, "gpt": GPT35(openai_key, preset, proxy)}

    async def send_message(self, group: Group | int, member: Member | int, content: str) -> str:
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        if group not in self.data or member not in self.data[group]:
            _ = await self.new(group, member)
        if self.data[group][member]["running"]:
            return "我上一句话还没结束呢，别急阿~等我回复你以后你再说下一句话喵~"
        self.data[group][member]["running"] = True
        try:
            result = await self.data[group][member]["gpt"].send_message(content)
        except Exception as e:
            result = f"发生错误：{e}，请稍后再试"
        finally:
            self.data[group][member]["running"] = False
        return result
