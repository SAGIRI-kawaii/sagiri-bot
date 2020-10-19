from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def update_user_called_data(group_id: int, member_id: int, operation: str, count: int) -> None:
    """
    Update user called data

    Args:
        group_id: Group id
        member_id: Member id
        operation: Operation name
        count: Num to add

    Examples:
        await update_user_called_data(groupId,sender,"at",1)

    Return:
        None
    """
    sql_key_word = ["real", "at"]
    sql = "select memberId from userCalled where groupId=%d and memberId=%d" % (group_id, member_id)
    data = await execute_sql(sql)
    if data[0] is None:
        sql = "insert into userCalled (groupId,memberId) values (%d,%d)" % (group_id, member_id)
        await execute_sql(sql)
    if operation in sql_key_word:
        operation = '`' + operation + '`'
    sql = "UPDATE userCalled SET %s=%s+%d WHERE groupId=%d and memberId=%d" % (operation, operation, count, group_id, member_id)
    await execute_sql(sql)
