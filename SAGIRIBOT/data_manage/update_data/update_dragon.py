import datetime
from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def update_dragon_data(group_id: int, member_id: int, operation: str) -> None:
    """
    Update dragon king count data in database

    Args:
        group_id: ID of the group the member belongs to
        member_id: ID of the member
        operation: Refresh all data to 0 or add 1 to sb's data

    Examples:
        update_dragon_data(0, 0, operation: "all")
        update_dragon_data(group_id, member_id, operation: "normal")

    Return:
        None
    """
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if operation == "all":
        sql = "update dragon set count=0 where groupId=%d" % group_id
    else:
        sql = """INSERT INTO dragon (time, groupId, memberId) SELECT
                        '%s',%d,%d
                    FROM
                        DUAL
                    WHERE
                        NOT EXISTS (
                            SELECT
                                groupId, memberId
                            FROM
                                dragon
                            WHERE
                                groupId = %d
                            AND  memberId = %d
                            )""" % (time_now, group_id, member_id, group_id, member_id)
        await execute_sql(sql)
        sql = "update dragon set count=count+1 where groupId=%d and memberId=%d" % (group_id, member_id)
    await execute_sql(sql)
