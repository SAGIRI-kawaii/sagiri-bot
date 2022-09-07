from loguru import logger
from sqlalchemy import select

from graia.ariadne.model import Group, Member

from shared.orm import orm, UserPermission


@logger.catch
async def user_permission_require(group: int | Group, member: int | Member, level: int) -> bool:
    group = group.id if isinstance(group, Group) else group
    member = member.id if isinstance(member, Member) else member
    if result := await orm.fetchone(
        select(UserPermission.level).where(
            UserPermission.group_id == group, UserPermission.member_id == member
        )
    ):
        return result[0] >= level
    await orm.insert_or_ignore(
        UserPermission,
        [UserPermission.group_id == group, UserPermission.member_id == member],
        {"group_id": group, "member_id": member, "level": 1},
    )
    return level <= 1
