from typing import List

from graia.ariadne import Ariadne
from graia.ariadne.message.element import Image
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, Member, GroupMessage


class ConfirmWaiter(Waiter.create([GroupMessage])):

    def __init__(self, group: Group, member: Member, confirm_words: List[str] | None = None):
        self.confirm_words = ["是", "y", "yes", "确认"] if confirm_words is None else confirm_words
        self.group_id = group.id
        self.member_id = member.id

    async def detected_event(self, group: Group, member: Member, message: MessageChain):
        if group.id == self.group_id and member.id == self.member_id:
            return message.display.strip() in self.confirm_words


class ImageWaiter(Waiter.create([GroupMessage])):

    def __init__(self, group: Group, member: Member):
        self.group_id = group.id
        self.member_id = member.id

    async def detected_event(self, group: Group, member: Member, message: MessageChain):
        if group.id == self.group_id and member.id == self.member_id:
            return message[Image][0] if message.has(Image) else None
