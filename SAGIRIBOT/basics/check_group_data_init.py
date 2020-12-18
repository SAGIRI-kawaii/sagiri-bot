from itertools import chain

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql
from SAGIRIBOT.basics.get_config import get_config


async def check_group_data_init(group_list: list) -> None:
    sql = "select groupId from setting"
    data = await execute_sql(sql)
    group_id = list(chain.from_iterable(data))
    print(group_id)
    for i in group_list:
        print(i.id, ':', i.name)
        if i.id not in group_id:
            sql = """
            INSERT INTO setting 
            (groupId,groupName,`repeat`,setuLocal,bizhiLocal,countLimit,`limit`,setu,bizhi,
            `real`,r18,search,imgPredict,yellowPredict,searchBangumi,imgLightning,music,speakMode,switch,forbiddenCount) 
            VALUES 
            (%d,'%s',%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,'%s','%s','%s',0)
            """ % (i.id, i.name, True, True, True, True, 6, False, False,
                   False, False, False, False, False, False, False, "off", "normal", "online")
            await execute_sql(sql)
            sql = """
            INSERT INTO admin 
            (groupId,adminId) 
            VALUES 
            (%d,%d)
            """ % (i.id, await get_config("HostQQ"))
            await execute_sql(sql)
        else:
            sql = "update setting set groupName='%s' where groupId=%s" % (i.name, i.id)
            await execute_sql(sql)
    # group_id_now = set()
    # for i in group_list:
    #     group_id_now.add(i.id)
    # print(group_id_now)
    # for i in group_id:
    #     if i not in group_id_now:
    #         sql = "delete from setting where groupId=%s" % i
    #         await execute_sql(sql)
    #         sql = "delete from admin where groupId=%s" % i
    #         await execute_sql(sql)
