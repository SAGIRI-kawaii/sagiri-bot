from itertools import chain
from functions.basics.aio_mysql_excute import execute_sql


async def get_admin(group_id: int) -> list:
    """
    Get admin by group id from database

    Args:
        group_id: Group id

    Examples:
        admins = await get_admin(12345678)

    Return:
        list
    """
    sql = "SELECT adminId from admin WHERE groupId=%d" % group_id
    data = execute_sql(sql)
    admins = list(chain.from_iterable(data))
    return admins
