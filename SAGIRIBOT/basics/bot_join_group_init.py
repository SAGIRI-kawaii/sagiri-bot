from SAGIRIBOT.basics.aio_mysql_excute import execute_sql
from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.basics.frequency_limit_module import GlobalFrequencyLimitDict


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
    INSERT IGNORE INTO setting 
    (groupId,groupName,`repeat`,setuLocal,bizhiLocal,countLimit,`limit`,setu,bizhi,
    `real`,r18,search,imgPredict,yellowPredict,searchBangumi,imgLightning,longTextType,
    music,speakMode,switch,forbiddenCount) 
    VALUES 
    (%d,'%s',%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,'%s','%s','%s','%s',0)
    """ % (group_id, group_name, True, True, True, True, 6, False, False,
           False, False, False, False, False, False, False, "img", "off", "normal", "online")
    await execute_sql(sql)
    sql = """
    INSERT INTO admin 
    (groupId,adminId) 
    VALUES 
    (%d,%d)
    """ % (group_id, await get_config("HostQQ"))
    await execute_sql(sql)
    print("join group database init finished!")