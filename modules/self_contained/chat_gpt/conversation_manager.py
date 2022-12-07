import asyncio
from typing import TypedDict
from chatgpt.api import ChatGPT
from chatgpt.exceptions import StatusCodeException

from creart import create
from graia.ariadne.model.relationship import Group, Member

from core import Sagiri

config = create(Sagiri).config
proxy = config.proxy if config.proxy != "proxy" else None
openai_cookie = config.functions.get("openai_cookie")


def create_gpt(session_token: str, response_timeout: int = 100, proxies: str | None = None):
    return ChatGPT(response_timeout=response_timeout, session_token=session_token, proxies=proxies)


class MemberGPT(TypedDict):
    running: bool
    gpt: ChatGPT


class ConversationManager(object):
    def __init__(self):
        self.data: dict[int, dict[int, MemberGPT]] = {}

    def new(self, group: Group | int, member: Member | int):
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        if group in self.data:
            if member in self.data[group]:
                self.data[group][member]["gpt"].new_conversation()
            else:
                self.data[group][member] = {"running": False, "gpt": create_gpt(openai_cookie, proxies=proxy)}
        else:
            self.data[group] = {}
            self.data[group][member] = {"running": False, "gpt": create_gpt(openai_cookie, proxies=proxy)}

    def close(self, group: Group | int, member: Member | int):
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        if group in self.data and member in self.data[group]:
            self.data[group][member]["gpt"].close()

    async def send_message(self, group: Group | int, member: Member | int, content: str) -> str:
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        if group not in self.data or member not in self.data[group]:
            self.new(group, member)
        if self.data[group][member]["running"]:
            return "我上一句话还没结束呢，别急阿~等我回复你以后你再说下一句话喵~"
        self.data[group][member]["running"] = True
        try:
            result = (await asyncio.to_thread(self.data[group][member]["gpt"].send_message, content)).content
            self.data[group][member]["running"] = False
            return result
        except StatusCodeException as e:
            self.data[group][member]["running"] = False
            return f"发生错误：{e}，请稍后再试"
