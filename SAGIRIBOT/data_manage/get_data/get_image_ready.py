from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_image_ready(group_id, sender, target_db):
    """
    Check the database status if the user is ready

    Args:
        group_id: Group id
        sender: Sender
        target_db: Target database

    Examples:
        status = await get_image_ready(12345678, 12345678, "searchReady")
    """
    sql = "SELECT `status` from %s WHERE groupId=%d and memberId=%d" % (target_db, group_id, sender)
    try:
        result = await execute_sql(sql)
        # print(result)
        result = result[0]
    except TypeError:
        sql = "INSERT INTO %s (groupId,memberId,`status`) VALUES (%d,%d,%d)" % (target_db, group_id, sender, False)
        await execute_sql(sql)
        return False
    return result
