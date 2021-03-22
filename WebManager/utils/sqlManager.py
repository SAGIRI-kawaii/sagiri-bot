import aiomysql
import asyncio
import json


async def get_config():
    with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
        configs = json.loads(f.read())
    return configs


class Pmysql:
    """
    Asynchronous encapsulation class of MySQL based on aiomysql
    """

    __connection = None

    def __init__(self):
        self.cursor = None
        self.connection = None
        self.pool = None

    @staticmethod
    async def getconnection():
        if Pmysql.__connection is None:
            configs = await get_config()
            host = configs["dbHost"]
            user = configs["dbUser"]
            passwd = configs["dbPass"]
            db = configs["dbName"]
            loop = asyncio.get_event_loop()
            pool = await aiomysql.create_pool(
                host=host,
                user=user,
                password=passwd,
                db=db,
                port=3306,
                loop=loop
            )
            if pool:
                Pmysql.__pool = pool
                return pool
            else:
                raise Exception("connect to mysql error ")
        else:
            return Pmysql.__connection

    async def query(self, query, args=None):
        self.cursor = await self.connection.cursor()
        await self.cursor.execute(query, args)
        r = await self.cursor.fetchall()
        await self.cursor.close()
        return r

    async def execute(self, query, param=None):
        """
        增删改 操作
        :param query: sql语句
        :param param: 参数
        :return:
        """
        self.cursor = await self.connection.cursor()
        try:
            await self.cursor.execute(query, param)
            if self.cursor.rowcount == 0:
                return False
            else:
                await self.connection.commit()
                return True
        except Exception as e:
            print(e)
            return False
        finally:
            await self.cursor.close()


async def execute_sql(sql: str):
    """
    Execute MySQL statement asynchronously

    Args:
        sql: SQL statement to execute

    Examples:
        execute_sql("select * from table_name")

    Returns:
        Query results (tuple)
    """
    pool = await Pmysql.getconnection()
    if sql[:6].lower() == "select":
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                res = await cur.fetchall()
    else:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.Cursor) as cursor:
                res = await cursor.execute(sql)
                await conn.commit()
                return res
    pool.close()
    return res
