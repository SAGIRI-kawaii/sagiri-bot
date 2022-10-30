import yaml
from os import environ
from asyncio import Lock
from typing import NoReturn
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import select, update, insert, delete, inspect
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BIGINT, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

from creart import create
from .adapter import get_adapter
from shared.models.config import GlobalConfig


yaml.warnings({"YAMLLoadWarning": False})
environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"


class AsyncORM(object):
    """对象关系映射（Object Relational Mapping）"""

    engine: AsyncEngine | None = None
    session: AsyncSession | None = None
    base: DeclarativeMeta | None = None
    db_mutex: Lock | None = None
    async_session: None = None

    def __init__(
        self,
        db_link: str,
        engine: AsyncEngine | None = None,
        session: AsyncSession | None = None,
        base: DeclarativeMeta | None = None,
        async_session: None = None,
        db_mutex: Lock | None = None
    ):
        self.db_link = db_link
        self.db_mutex = db_mutex or Lock() if self.db_link.startswith("sqlite") else None
        self.engine = engine or create_async_engine(self.db_link, **get_adapter(self.db_link), echo=False)
        self.session = session or AsyncSession(bind=self.engine)
        self.base = base or declarative_base(self.engine)
        self.async_session = async_session or sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    def initialize(
        self,
        engine: AsyncEngine | None = None,
        session: AsyncSession | None = None,
        base: DeclarativeMeta | None = None,
        async_session: None = None
    ):
        self.engine = engine or create_async_engine(self.db_link, **get_adapter(self.db_link), echo=False)
        self.session = session or AsyncSession(bind=self.engine)
        self.base = base or declarative_base(self.engine)
        self.async_session = async_session or sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def create_all(self):
        """创建所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.create_all)

    async def drop_all(self):
        """删除所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.drop_all)

    async def add(self, table, dt):
        """插入"""
        async with self.async_session() as session:
            async with session.begin():
                session.add(table(**dt), _warn=False)
            await session.commit()

    async def execute(self, sql, **kwargs):
        async with AsyncSession(self.engine) as session:
            try:
                if self.db_mutex:
                    await self.db_mutex.acquire()
                result = await session.execute(sql, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                # await session.close()
                raise e
            finally:
                if self.db_mutex:
                    self.db_mutex.release()

    async def fetchall(self, sql):
        return (await self.execute(sql)).fetchall()

    async def fetchone(self, sql):
        result = await self.execute(sql)
        return one if (one := result.fetchone()) else None

    async def fetchone_dt(self, sql, n=999999):
        result = await self.execute(sql)
        columns = result.keys()
        length = len(columns)
        for _ in range(n):
            if one := result.fetchone():
                yield {columns[i]: one[i] for i in range(length)}

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
        for table in self.base.__subclasses__():
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


orm = AsyncORM(create(GlobalConfig).db_link)

Base = orm.base


class ChatRecord(Base):
    """聊天记录表"""

    __tablename__ = "chat_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(BIGINT, nullable=False)
    member_id = Column(BIGINT, nullable=False)
    persistent_string = Column(String(length=4000), nullable=False)
    seg = Column(String(length=4000), nullable=False)


class BlackList(Base):
    """黑名单表"""

    __tablename__ = "black_list"

    member_id = Column(BIGINT, primary_key=True)
    group_id = Column(BIGINT, primary_key=True)
    is_global = Column(Boolean, default=False)


class UserPermission(Base):
    """用户等级表（管理权限）"""

    __tablename__ = "user_permission"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT, primary_key=True)
    level = Column(Integer, default=1)


class Setting(Base):
    """群组设置"""

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
    """群员调用记录"""

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
    """关键词回复"""

    __tablename__ = "keyword_reply"

    keyword = Column(String(length=200), primary_key=True)
    group = Column(BIGINT, default=-1)
    reply_type = Column(String(length=10), nullable=False)
    reply = Column(Text, nullable=False)
    reply_md5 = Column(String(length=32), primary_key=True)


class TriggerKeyword(Base):
    """关键词触发功能"""

    __tablename__ = "trigger_keyword"

    keyword = Column(String(length=60), primary_key=True)
    function = Column(String(length=20))


class FunctionCalledRecord(Base):
    """功能调用记录"""

    __tablename__ = "function_called_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(BIGINT, nullable=False)
    member_id = Column(BIGINT, nullable=False)
    function = Column(String(length=40), nullable=False)
    result = Column(Boolean, default=True)


class LoliconData(Base):
    """lolicon api数据"""

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
    """wordle 游戏数据"""

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
    """group_team 群小组"""

    __tablename__ = "group_team"

    creator = Column(BIGINT)
    group_id = Column(BIGINT, primary_key=True)
    name = Column(String(length=200), primary_key=True)
    teammates = Column(Text)


class ChatClips(Base):
    """chat_clips 群片段记录"""

    __tablename__ = "chat_clips"

    cid = Column(Integer, primary_key=True)
    group_id = Column(BIGINT)
    member_id = Column(BIGINT)
    uid = Column(BIGINT)


class BilibiliSubscribe(Base):
    """bilibili_subscribe Bilibili订阅"""

    __tablename__ = "bilibili_subscribe"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT)
    uid = Column(BIGINT, primary_key=True)


class GroupMembersBackup(Base):
    """group_member_backup 群成员备份"""

    __tablename__ = "group_member_backup"

    group_id = Column(BIGINT, primary_key=True)
    group_name = Column(String(length=60), nullable=False)
    members = Column(String, nullable=False)


class APIAccount(Base):
    """api_account 管理面板账户"""

    __tablename__ = "api_account"

    applicant = Column(BIGINT)
    username = Column(String(length=60), primary_key=True)
    password = Column(String)
