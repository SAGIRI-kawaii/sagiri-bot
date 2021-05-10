import yaml
from os import environ
from loguru import logger

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

yaml.warnings({'YAMLLoadWarning': False})
environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'

# DB_LINK = 'oracle://test:123456@localhost:1521/xe'
# DB_LINK = "mysql+aiomysql://root:pass@localhost:3306/test"
# DB_LINK = "sqlite:///data.db"


def get_config(config: str):
    with open('config.yaml', 'r', encoding='utf-8') as f:  # 从json读配置
        configs = yaml.load(f.read())
    if config in configs.keys():
        return configs[config]
    else:
        logger.error(f"getConfig Error: {config}")


# DB_LINK = get_config("DBLink")
DB_LINK = "sqlite+aiosqlite:///data.db"


class AsyncEngine:
    def __init__(self, db_link):
        self.engine = create_async_engine(
            db_link,
            echo=True
        )

    async def execute(self, sql, **kwargs):
        async with AsyncSession(self.engine) as session:
            result = await session.execute(sql, **kwargs)
            return result

    async def fetchall(self, sql):
        return (await self.execute(sql)).fetchall()

    async def fetchone(self, sql):
        # self.warning(sql)
        result = await self.execute(sql)
        one = result.fetchone()
        if one:
            return one

    async def fetchone_dt(self, sql, n=999999):
        # self.warning(sql)
        result = await self.execute(sql)
        columns = result.keys()
        length = len(columns)
        for _ in range(n):
            one = result.fetchone()
            if one:
                yield {columns[i]: one[i] for i in range(length)}

    @staticmethod
    def warning(x):
        print('\033[033m{}\033[0m'.format(x))

    @staticmethod
    def error(x):
        print('\033[031m{}\033[0m'.format(x))


class AsyncORM(AsyncEngine):
    """对象关系映射（Object Relational Mapping）"""

    def __init__(self, conn):
        super().__init__(conn)
        self.session = AsyncSession(bind=self.engine) # 创建ORM对象
        self.Base = declarative_base(self.engine)
        # self.create_all()

    # def __del__(self):
    #     self.session.close()

    def create_all(self):
        """创建所有表"""
        self.Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """创建所有表"""
        self.Base.metadata.drop_all(bind=self.engine)

    async def add(self, table, dt):
        """插入"""
        await self.session.add(table(**dt))  # 添加到ORM对象
        await self.session.commit()  # 提交

    async def update(self, table, condition, dt):
        """有则更新，没则插入"""
        q = await self.session.query(table).filter_by(**condition)
        if q.all():
            q.update(dt)
            await self.session.commit()
        else:
            await self.add(table, dt)

    async def delete(self, table, condition):
        q = self.session.query(table).filter_by(**condition)
        if q.all():
            q.delete()
            await self.session.commit()


orm1 = AsyncORM(DB_LINK)
from .Tables import *
# orm.create_all()
