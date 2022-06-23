import yaml
from os import environ
from loguru import logger
from typing import NoReturn
from asyncio import Semaphore
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import select, update, insert, delete, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BIGINT, Text

from .adapter import get_adapter

yaml.warnings({'YAMLLoadWarning': False})
environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'


# DB_LINK = 'oracle://test:123456@localhost:1521/xe'
# DB_LINK = "mysql+aiomysql://root:pass@localhost:3306/test"
# DB_LINK = "sqlite:///data.db"


def get_config(config: str):
    with open('config.yaml', 'r', encoding='utf-8') as f:  # 从json读配置
        configs = yaml.load(f.read(), Loader=yaml.BaseLoader)
    if config in configs.keys():
        return configs[config]
    else:
        logger.error(f"getConfig Error: {config}")


DB_LINK = get_config("db_link")
# DB_LINK = "sqlite+aiosqlite:///data.db"

db_mutex = Semaphore(1) if DB_LINK.startswith("sqlite") else None


class AsyncEngine:
    def __init__(self, db_link):
        self.engine = create_async_engine(
            db_link,
            **get_adapter(db_link),
            echo=False
        )

    async def execute(self, sql, **kwargs):
        async with AsyncSession(self.engine) as session:
            try:
                if db_mutex:
                    await db_mutex.acquire()
                result = await session.execute(sql, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                # await session.close()
                raise e
            finally:
                if db_mutex:
                    db_mutex.release()

    async def fetchall(self, sql):
        return (await self.execute(sql)).fetchall()

    async def fetchone(self, sql):
        # self.warning(sql)
        result = await self.execute(sql)
        one = result.fetchone()
        if one:
            return one
        else:
            return None

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
        self.session = AsyncSession(bind=self.engine)
        self.Base = declarative_base(self.engine)
        self.async_session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        # self.create_all()

    # def __del__(self):
    #     self.session.close()

    async def create_all(self):
        """创建所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.create_all)

    async def drop_all(self):
        """删除所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.drop_all)

    async def add(self, table, dt):
        """插入"""
        async with self.async_session() as session:
            async with session.begin():
                session.add(table(**dt), _warn=False)
            await session.commit()

    async def update(self, table, condition, dt):
        await self.execute(update(table).where(*condition).values(**dt))

    async def insert_or_update(self, table, condition, dt):
        if (await self.execute(select(table).where(*condition))).all():
            return await self.execute(update(table).where(*condition).values(**dt))
        else:
            return await self.execute(insert(table).values(**dt))

    async def insert_or_ignore(self, table, condition, dt):
        if not (await self.execute(select(table).where(*condition))).all():
            return await self.execute(insert(table).values(**dt))

    async def delete(self, table, condition):
        return await self.execute(delete(table).where(*condition))

    async def init_check(self) -> NoReturn:
        for table in self.Base.__subclasses__():
            if not await self.table_exists(table.__tablename__):
                table.__table__.create(self.engine)
        return None

    @staticmethod
    def use_inspector(conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async def table_exists(self, table_name: str) -> bool:
        async with self.engine.connect() as conn:
            tables = await conn.run_sync(self.use_inspector)
        return table_name in tables


orm = AsyncORM(DB_LINK)

Base = orm.Base


class ChatRecord(Base):
    """ 聊天记录表 """
    __tablename__ = "chat_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(BIGINT, nullable=False)
    member_id = Column(BIGINT, nullable=False)
    persistent_string = Column(String(length=4000), nullable=False)
    seg = Column(String(length=4000), nullable=False)


class BlackList(Base):
    """ 黑名单表 """
    __tablename__ = "black_list"

    member_id = Column(BIGINT, primary_key=True)
    group_id = Column(BIGINT, primary_key=True)
    is_global = Column(Boolean, default=False)


class UserPermission(Base):
    """ 用户等级表（管理权限） """
    __tablename__ = "user_permission"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT, primary_key=True)
    level = Column(Integer, default=1)


class Setting(Base):
    """ 群组设置 """
    __tablename__ = "setting"

    group_id = Column(BIGINT, primary_key=True)
    group_name = Column(String(length=60), nullable=False)
    repeat = Column(Boolean, default=True)
    frequency_limit = Column(Boolean, default=True)
    setu = Column(Boolean, default=False)
    real = Column(Boolean, default=False)
    real_high_quality = Column(Boolean, default=False)
    bizhi = Column(Boolean, default=False)
    r18 = Column(Boolean, default=False)
    img_search = Column(Boolean, default=False)
    bangumi_search = Column(Boolean, default=False)
    compile = Column(Boolean, default=False)
    dice = Column(Boolean, default=False)
    avatar_func = Column(Boolean, default=False)
    anti_revoke = Column(Boolean, default=False)
    anti_flash_image = Column(Boolean, default=False)
    online_notice = Column(Boolean, default=False)
    daily_newspaper = Column(Boolean, default=False)
    setting = Column(Text, default="{}")
    debug = Column(Boolean, default=False)
    switch = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    music = Column(String(length=10), default="off")
    r18_process = Column(String(length=10), default="revoke")
    speak_mode = Column(String(length=10), default="normal")
    long_text_type = Column(String(length=5), default="text")
    voice = Column(String(length=10), default="off")


class UserCalledCount(Base):
    """ 群员调用记录 """
    __tablename__ = "user_called_count"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT, primary_key=True)
    setu = Column(Integer, default=0)
    real = Column(Integer, default=0)
    bizhi = Column(Integer, default=0)
    at = Column(Integer, default=0)
    search = Column(Integer, default=0)
    song_order = Column(Integer, default=0)
    chat_count = Column(Integer, default=0)
    functions = Column(Integer, default=0)


class KeywordReply(Base):
    """ 关键词回复 """
    __tablename__ = "keyword_reply"

    keyword = Column(String(length=200), primary_key=True)
    group = Column(BIGINT, default=-1)
    reply_type = Column(String(length=10), nullable=False)
    reply = Column(Text, nullable=False)
    reply_md5 = Column(String(length=32), primary_key=True)


class TriggerKeyword(Base):
    """ 关键词触发功能 """
    __tablename__ = "trigger_keyword"

    keyword = Column(String(length=60), primary_key=True)
    function = Column(String(length=20))


class FunctionCalledRecord(Base):
    """ 功能调用记录 """
    __tablename__ = "function_called_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(BIGINT, nullable=False)
    member_id = Column(BIGINT, nullable=False)
    function = Column(String(length=40), nullable=False)
    result = Column(Boolean, default=True)


class LoliconData(Base):
    """ lolicon api数据 """
    __tablename__ = "lolicon_data"

    pid = Column(BIGINT, primary_key=True)
    p = Column(Integer, primary_key=True)
    uid = Column(BIGINT, nullable=False)
    title = Column(String(length=200), nullable=False)
    author = Column(String(length=200), nullable=False)
    r18 = Column(Boolean, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    tags = Column(String(length=1000), nullable=False)
    ext = Column(String(length=20), nullable=False)
    upload_date = Column(DateTime, nullable=False)
    original_url = Column(String(length=200), nullable=False)


class WordleStatistic(Base):
    """ wordle 游戏数据 """
    __tablename__ = "wordle_statistic"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT, primary_key=True)
    game_count = Column(BIGINT, default=0)
    win_count = Column(BIGINT, default=0)
    lose_count = Column(BIGINT, default=0)
    correct_count = Column(BIGINT, default=0)
    wrong_count = Column(BIGINT, default=0)
    hint_count = Column(BIGINT, default=0)


class GroupTeam(Base):
    """ group_team 群小组 """
    __tablename__ = "group_team"

    creator = Column(BIGINT)
    group_id = Column(BIGINT, primary_key=True)
    name = Column(String(length=200), primary_key=True)
    teammates = Column(Text)


# class SchedulerTasks(Base):
#     """ 计划任务 """
#     __tablename__ = "scheduler_tasks"
# print("\n".join([f"{i}: {type(getattr(JLUEpidemicAccountInfo, i))}" for i in dir(JLUEpidemicAccountInfo)]))
