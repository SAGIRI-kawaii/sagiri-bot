from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def check996(keyword: str) -> list:
    sql = f"SELECT * FROM db996 WHERE `name` LIKE '%{keyword}%'"
    result = await execute_sql(sql)
    if result:
        text = f"共找到{len(result)}条结果：\n\n"
        index = 0
        for i in result:
            index += 1
            text += f"{index}.\n"
            text += f"公司名称：{i[1]}\n"
            text += f"所在城市：{i[0]}\n"
            text += f"曝光/施行时间：{i[2]}\n"
            text += f"制度描述：{i[3]}\n\n"
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=text),
                Plain(text="声明：无记录并不代表非996，所有数据皆从github项目996.ICU获取，请自行甄别")
            ])
        ]
    else:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=f"没有找到{keyword}的信息呢~\n"),
                Plain(text="可能公司不是996哦~（可能哦~）\n"),
                Plain(text="声明：无记录并不代表非996，所有数据皆从github项目996.ICU获取，请自行甄别")
            ])
        ]