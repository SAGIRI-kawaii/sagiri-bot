import asyncio
import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from graia.ariadne.model import Group, Member

from shared.orm import orm
from shared.orm.tables import UserCalledCount, FunctionCalledRecord


async def update_user_call_count_plus(
    group: Group, member: Member, table_column, column_name: str, count: int = 1
) -> bool:
    for _ in range(5):
        new_value = await orm.fetchone(
            select(table_column).where(
                UserCalledCount.group_id == group.id,
                UserCalledCount.member_id == member.id,
            )
        )
        new_value = new_value[0] + count if new_value else count
        try:
            res = await orm.insert_or_update(
                UserCalledCount,
                [UserCalledCount.group_id == group.id, UserCalledCount.member_id == member.id],
                {"group_id": group.id, "member_id": member.id, column_name: new_value},
            )
            if not res:
                return False
            if column_name != "chat_count":
                await orm.add(
                    FunctionCalledRecord,
                    {
                        "time": datetime.datetime.now(),
                        "group_id": group.id,
                        "member_id": member.id,
                        "function": column_name,
                    },
                )
            return True
        except IntegrityError:
            await asyncio.sleep(1)
            continue
