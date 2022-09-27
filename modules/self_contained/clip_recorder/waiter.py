from graia.ariadne import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, Member, GroupMessage

from shared.utils.message_chain import message_chain_to_json


class WordleWaiter(Waiter.create([GroupMessage])):

    def __init__(self, name: str, group: Group | int, running: dict[int, bool]):
        self.name = name
        self.group = group if isinstance(group, int) else group.id
        self.running = running
        self.data = []

    async def detected_event(
        self,
        app: Ariadne,
        group: Group,
        member: Member,
        message: MessageChain
    ):
        if not self.running[self.group] or group.id != self.group:
            return self.data
        self.data.append(message_chain_to_json(message))
