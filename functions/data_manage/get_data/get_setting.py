from functions.basics.aio_mysql_excute import execute_sql


async def get_setting(group_id: int, setting_name: str):
    """
    Return setting from database

    Args:
        group_id: group id
        setting_name: setting name

    Examples:
        setting = get_setting(12345678, "repeat")

    Return:
        Operation result
    """
    sql_key_word = ["repeat", "real", "limit"]
    if setting_name in sql_key_word:
        setting_name = '`'+setting_name+'`'
    sql = "SELECT %s from setting WHERE groupId=%d" % (setting_name, group_id)
    data = await execute_sql(sql)
    return data[0][0]
