import datetime

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def register(group_id: int, member_id: int) -> list:
    now = datetime.datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    today = datetime.datetime.strptime(today_date, "%Y-%m-%d")
    print(today)
    sql = f"SELECT `date` FROM registerRecord WHERE groupId={group_id} AND memberId={member_id} AND `date`>='{today}'"
    res = await execute_sql(sql)
    print(res)
    if len(res) != 0:
        return [
            "None",
            MessageChain.create([
                At(target=member_id),
                Plain(text="你今天已经签过到了呢~请不要重复签到哦~")
            ])
        ]
    else:
        sql = f"SELECT count(*) FROM registerRecord WHERE groupId={group_id} AND `date`>='{today}'"
        res = await execute_sql(sql)
        rank = res[0][0] + 1
        sql = f"INSERT IGNORE INTO registerRecord (groupId,memberId,`date`) VALUES ({group_id},{member_id},'{now}')"
        await execute_sql(sql)
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=f"签到成功！你是本群今日第{rank}个签到的哦~")
            ])
        ]
