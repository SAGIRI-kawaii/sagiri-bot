import aiomysql
from SAGIRIBOT.basics.get_config import get_config


class Pmysql:
    """
    Asynchronous encapsulation class of MySQL based on aiomysql
    """

    __connection = None

    def __init__(self):
        self.cursor = None
        self.connection = None

    @staticmethod
    async def getconnection():
        if Pmysql.__connection is None:
            host = await get_config("dbHost")
            user = await get_config("dbUser")
            passwd = await get_config("dbPass")
            db = await get_config("dbName")
            conn = await aiomysql.connect(
                host=host,
                user=user,
                password=passwd,
                db=db,
                port=3306,
                )
            if conn:
                Pmysql.__connection = conn
                return conn
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
    mysql_obj = Pmysql()
    conn = await Pmysql.getconnection()
    mysql_obj.connection = conn
    await conn.ping()
    if sql[:6] == "select" or sql[:6] == "SELECT":
        res = await mysql_obj.query(sql)
    else:
        res = await mysql_obj.execute(sql)

        # print(res)
    conn.close()
    return res
