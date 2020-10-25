import datetime
from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def write_log(operation, pic_url, sender, group_id, result, operationType):
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if operationType == 'img':
        pic_url = pic_url.replace("\\", "\\\\")
        sql = """INSERT INTO imgCalled 
                (time,operation,picUrl,sender,groupId,result) 
                    VALUES 
                ('%s','%s','%s',%d,%d,%d)""" % (time_now, operation, pic_url, sender, group_id, result)
    elif operationType == 'function':
        sql = """INSERT INTO functionCalled 
                (time,operation,sender,groupId,result) 
                    VALUES 
                ('%s','%s',%d,%d,%d)""" % (time_now, operation, sender, group_id, result)
    await execute_sql(sql)
    print("data recorded!")
