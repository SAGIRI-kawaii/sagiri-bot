import yaml
from os import environ
from asyncio import Lock
from typing import NoReturn
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import select, update, insert, delete, inspect, text
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
            _ = await conn.run_sync(self.base.metadata.create_all)

    async def drop_all(self):
        """删除所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.drop_all)

    async def add(self, table, dt):
        """插入"""
        await self.execute(insert(table).values(**dt))

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

    async def reset_version(self):
        async with self.engine.connect() as conn:
            _ = await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))


orm = AsyncORM(create(GlobalConfig).db_link)

Base = orm.base
