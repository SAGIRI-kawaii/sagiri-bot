from functions.basics.aio_mysql_excute import execute_sql


async def set_get_img_ready(group_id, sender, status, target_db):
    """
    Change status of member search/predict/yellow predict/tribute ready in database

    Args:
        group_id: Group id
        sender: Sender
        status: Status to modify
        target_db: Target database

    Examples:
        set_search_ready(12345678, 12345678, True, "searchReady")

    """
    sql = "SELECT `status` from %s WHERE groupId=%d and memberId=%d" % (target_db, group_id, sender)
    try:
        result = await execute_sql(sql)
        # print(result)
        result = result[0][0]
        # print(result)
        sql = "UPDATE %s SET `status`=%d WHERE groupId=%d and memberId=%d" % (target_db, status, group_id, sender)
        status = await execute_sql(sql)
        print(status)
    except TypeError:
        sql = "INSERT INTO %s (groupId,memberId,Status) VALUES (%d,%d,%d)" % (target_db, group_id, sender, status)
        await execute_sql(sql)
    print(sql)
