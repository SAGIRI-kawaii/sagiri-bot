from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def save_birthday(member_id: int, group_id: int, birthday: str) -> None:
    sql = f"""REPLACE INTO birthday (memberId, groupId, birthday, announce) 
                VALUES 
            ({member_id}, {group_id}, '{birthday}', false)"""
    # print(sql)
    await execute_sql(sql)
