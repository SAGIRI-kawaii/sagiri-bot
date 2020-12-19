from itertools import chain
from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_blacklist() -> list:
    """
    Get blacklist from database

    Args:
        None

    Examples:
        blacklist = await get_blacklist()

    Return:
        list
    """
    sql = "SELECT id from blacklist"
    data = await execute_sql(sql)
    blacklist = list(chain.from_iterable(data))
    return blacklist
