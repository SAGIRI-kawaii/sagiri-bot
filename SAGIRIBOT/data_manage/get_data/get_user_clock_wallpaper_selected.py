from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_user_clock_wallpaper_selected(group_id: int, sender: int):
    """
    Return the clock wallpaper user selected

    Args:
        group_id: Group id
        sender: Sender

    Examples:
        choice = await get_user_clock_wallpaper_selected(group_id, sender)
    """
    sql = "SELECT choice from clockChoice WHERE groupId=%d and memberId=%d" % (group_id, sender)
    try:
        result = await execute_sql(sql)
        result = result[0]
        return result
    except TypeError:
        return None
