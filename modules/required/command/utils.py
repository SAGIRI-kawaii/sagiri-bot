from creart import create
from graia.ariadne import Ariadne
from graia.ariadne.event.message import Group
from graia.ariadne.message.element import At, Plain
from graia.ariadne.message.chain import MessageChain

from shared.models.public_group import PublicGroup


def get_targets(message: MessageChain) -> list[int]:
    ats = message.get(At)
    plains = message.get(Plain)
    print([at.target for at in ats] + [int(qid) for qid in "".join([plain.text for plain in plains]).strip().split(" ") if qid.isdigit()])
    return [at.target for at in ats] + [int(qid) for qid in "".join([plain.text for plain in plains]).strip().split(" ") if qid.isdigit()]


async def target_valid(target: int, group: Group | int) -> bool:
    public_group = create(PublicGroup)
    if isinstance(group, Group):
        group = group.id
    if group not in public_group.data:
        raise ValueError(f"group {group} not found!")
    if await Ariadne.current(list(public_group.data[group].keys())[0]).get_member(group, target):
        return True
    return False
