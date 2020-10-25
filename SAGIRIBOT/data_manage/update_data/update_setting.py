from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def update_setting(group_id, setting_name, new_setting_value) -> None:
    """
    Update setting to database

    Args:
        group_id: Group id
        setting_name: Setting name
        new_setting_value: New setting value

    Examples:
        await update_setting(12345678, "setu", True)

    Return:
        None
    """
    str_key_word = ["speakMode", "switch", "music", "r18Process"]
    sql_key_word = ["repeat", "real", "limit"]
    if setting_name in sql_key_word:
        setting_name = '`'+setting_name+'`'
    if setting_name in str_key_word:
        sql = "UPDATE setting SET %s='%s' WHERE groupId=%d" % (setting_name, new_setting_value, group_id)
    else:
        sql = "UPDATE setting SET %s=%s WHERE groupId=%d" % (setting_name, new_setting_value, group_id)
    await execute_sql(sql)
