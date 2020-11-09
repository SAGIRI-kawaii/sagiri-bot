from graia.application.event.messages import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_joke(name: str) -> list:
    sql = "select * from jokes order by rand() limit 1"
    joke = await execute_sql(sql)
    if joke == (None,):
        return [
            "None",
            MessageChain.create([
                Plain(text="笑话数据库为空！")
            ])
        ]
    else:
        joke = joke[0][0]
        joke = joke.replace("%name%", name).replace("\n", "")
        return [
            "None",
            MessageChain.create([
                Plain(text=joke)
            ])
        ]


async def get_key_joke(key: str) -> list:
    sql = "select * from %sJokes order by rand() limit 1" % key
    joke = await execute_sql(sql)
    if joke == (None,):
        return [
            "None",
            MessageChain.create([
                Plain(text="笑话数据库为空！")
            ])
        ]
    else:
        joke = joke[0][0]
        return [
            "None",
            MessageChain.create([
                Plain(text=joke)
            ])
        ]
