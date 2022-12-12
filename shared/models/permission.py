from abc import ABC
from typing import Type
from sqlalchemy import select

from graia.ariadne.model import Member, Group
from creart import add_creator, exists_module
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.orm import orm
from shared.orm.tables import UserPermission


class GroupPermission(object):
    data: dict[int, dict[int, int]]
    """
    {
        group: {
            member: level
        }
    }
    """

    def __init__(self):
        self.data = {}

    async def data_init(self):
        datas = await orm.fetchall(select(UserPermission.group_id, UserPermission.member_id, UserPermission.level))
        for data in datas:
            if data[0] in self.data:
                self.data[data[0]][data[1]] = data[2]
            else:
                self.data[data[0]] = {data[1]: data[2]}

    async def get_permission(self, group: Group | int, member: Member | int):
        if isinstance(member, Member):
            member = member.id
        if isinstance(group, Group):
            group = group.id
        if group in self.data and member in self.data[group]:
            return self.data[group][member]
        else:
            await self.update(group, member, 1)
            return 1

    async def update(self, group: Group | int, member: Member | int, level: int, is_global: bool = False):
        if isinstance(member, Member):
            member = member.id
        if isinstance(group, Group):
            group = group.id
        if not is_global:
            if group in self.data:
                self.data[group][member] = level
            else:
                self.data[group] = {member: level}
            await orm.insert_or_update(
                UserPermission,
                [UserPermission.member_id == member, UserPermission.group_id == group],
                {"member_id": member, "group_id": group, "level": level}
            )
        else:
            for group_id in self.data:
                self.data[group_id][member] = level
                await orm.insert_or_update(
                    UserPermission,
                    [UserPermission.member_id == member, UserPermission.group_id == group_id],
                    {"member_id": member, "group_id": group_id, "level": level}
                )


class GroupPermissionClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.models.permission", "GroupPermission"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.models.permission")

    @staticmethod
    def create(create_type: Type[GroupPermission]) -> GroupPermission:
        return GroupPermission()


add_creator(GroupPermissionClassCreator)
