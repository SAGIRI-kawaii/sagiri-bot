from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def bot_join_group_init(group_id: int, group_name: str) -> None:
    """
    When bot join a new group, insert data to database

    Args:
        group_id: Group id
        group_name: Group name

    Examples:
        await bot_join_group_init(12345678, "group")

    Return:
        None
    """
    sql = """
    INSERT INTO setting 
    (groupId,groupName,`repeat`,setuLocal,bizhiLocal,countLimit,`limit`,setu,bizhi,`real`,r18,search,speakMode,music,switch,forbiddenCount) 
    VALUES 
    (%d,'%s',%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,'%s','%s','%s',0)
    """ % (group_id, group_name, True, True, True, True, 6, True, True, True, False, True, "normal", "wyy", "online")
    await execute_sql(sql)
    print("join group database init finished!")