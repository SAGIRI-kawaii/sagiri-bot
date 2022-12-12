from abc import ABC
from sqlalchemy import select
from typing import Dict, Set, NoReturn, Type

from graia.ariadne.model import Member, Group
from creart import add_creator, exists_module
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.orm import orm
from shared.orm.tables import BlackList


class GroupBlackList(object):
    data: Dict[int, Set[int]]
    global_data: Set[int]

    def __init__(self):
        self.data = {}
        self.global_data = set()

    async def data_init(self) -> NoReturn:
        blacklist = await orm.fetchall(select(BlackList.member_id, BlackList.group_id))
        for b in blacklist:
            if b[1] == -1:
                self.global_data.add(b[0])
            if b[0] in self.data:
                self.data[b[0]].add(b[1])
            else:
                self.data[b[0]] = {b[1], }

    def blocked(self, member: Member | int, group: Group | int | None = None) -> bool:
        if isinstance(member, Member):
            member = member.id
        if isinstance(group, Group):
            group = group.id
        return member in self.data and group in self.data[member] or member in self.global_data

    async def add(self, member: Member | int, group: Group | int | None = None, is_global: bool = False) -> NoReturn:
        if isinstance(member, Member):
            member = member.id
        if isinstance(group, Group):
            group = group.id
        if not is_global:
            if member in self.data:
                self.data[member].add(group)
            else:
                self.data[member] = {group, }
        else:
            group = -1
            self.global_data.add(member)
        await orm.insert_or_update(
            BlackList,
            [BlackList.member_id == member, BlackList.group_id == group],
            {"member_id": member, "group_id": group}
        )

    async def remove(self, member: Member | int, group: Group | int | None = None, is_global: bool = False) -> NoReturn:
        if isinstance(member, Member):
            member = member.id
        if isinstance(group, Group):
            group = group.id
        if not is_global:
            if member in self.data:
                self.data[member].discard(group)
        else:
            group = -1
            self.global_data.discard(member)
        await orm.delete(BlackList, [BlackList.member_id == member, BlackList.group_id == group])

    async def clear(self, member: Member | int) -> NoReturn:
        """用于清除对应账号所有群组内的黑名单和全局黑名单

        Args:
            member(Member | int): 用户账号
        """
        if isinstance(member, Member):
            member = member.id
        self.global_data.discard(member)

        if member in self.data:
            del self.data[member]
        await orm.delete(BlackList, [BlackList.member_id == member])


class GroupBlackListClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.models.blacklist", "GroupBlackList"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.models.blacklist")

    @staticmethod
    def create(create_type: Type[GroupBlackList]) -> GroupBlackList:
        return GroupBlackList()


add_creator(GroupBlackListClassCreator)
