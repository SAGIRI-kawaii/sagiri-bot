import contextlib
from sqlalchemy import inspect
from asyncio import current_task
from typing import Any, TypeVar, cast
from sqlalchemy.engine.url import URL
from sqlalchemy.sql.base import Executable
from sqlalchemy.engine.result import Result
from collections.abc import AsyncGenerator, Sequence
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.sql.selectable import TypedReturnsRows
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from shared.database.model import Base
from shared.database.types import EngineOptions

# sqlite_url = 'sqlite+aiosqlite:///data/redbot.db'
# mysql_url = 'mysql+aiomysql://user:pass@hostname/dbname?charset=utf8mb4
T_Row = TypeVar("T_Row", bound=Base)


class DatabaseManager:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    _scoped_session: async_scoped_session

    def __init__(self, url: str | URL, engine_options: EngineOptions | None = None, session_options: dict[str, Any] | None = None):
        if engine_options is None:
            engine_options = {"echo": False, "pool_pre_ping": True}
        self.engine = create_async_engine(url, **engine_options)
        self._scoped_session = None
        if session_options is None:
            session_options = {"expire_on_commit": False}
        self.session_factory = async_sessionmaker(self.engine, **session_options)

    @classmethod
    def get_engine_url(
        cls,
        driver: str = "asnycmy",
        db_type: str = "mysql",
        host: str = "localhost",
        port: int = 3306,
        username: str | None = None,
        passwd: str | None = None,
        database_name: str | None = None,
        **kwargs: dict[str, str],
    ) -> str:
        if db_type == "mysql":
            if username is None or passwd is None or database_name is None:
                raise RuntimeError("Option `username` or `passwd` or `database_name` must in parameter.")
            url = f"mysql+{driver}://{username}:{passwd}@{host}:{port}/{database_name}"
        elif db_type == "sqlite":
            url = f"sqlite+{driver}://"
        else:
            raise RuntimeError("Unsupport database type, please creating URL manually.")
        kw = "".join(f"&{key}={value}" for key, value in kwargs.items()).lstrip("&")
        return url + kw if kw else url

    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def stop(self):
        # for AsyncEngine created in function scope, close and
        # clean-up pooled connections
        await self.engine.dispose()

    async def async_safe_session(self):
        """生成一个异步安全的session回话."""
        if not self._scoped_session:
            self._scoped_session = async_scoped_session(self.session_factory, scopefunc=current_task)
        return self._scoped_session

    @contextlib.asynccontextmanager
    async def async_session(self) -> AsyncGenerator[async_scoped_session[AsyncSession], Any]:
        """异步session上下文管理封装.

        Returns:
            >>> async with db_manager.async_session() as session:
            >>>     res = await session.execute("SELECT 1")
            >>>     print(res.scalar())
            1
        """
        scoped_session = await self.async_safe_session()
        try:
            yield scoped_session
            await self._scoped_session.commit()
        except Exception:
            await self._scoped_session.rollback()
            raise
        finally:
            await self._scoped_session.remove()

    async def exec(self, sql: Executable) -> Result:
        async with self.async_session() as session:
            return await session.execute(sql)

    # from sqlalchemy.sql.expression import Select
    # async def select_all(self, sql: Select[tuple[T_Row]]) -> list[Sequence[T_Row]]:
    #     result = await self.exec(sql)
    #     return cast(list[Sequence[T_Row]], result.all())
    # async def select_first(self, sql: Select[tuple[T_Row]]) -> Sequence[T_Row] | None:
    #     result = await self.exec(sql)
    #     return cast(Sequence[T_Row] | None, result.first())

    async def select_all(self, sql: TypedReturnsRows[tuple[T_Row]]) -> Sequence[T_Row]:
        async with (await self.async_safe_session())() as session:
            result = await session.scalars(sql)
        return result.all()

    async def select_first(self, sql: TypedReturnsRows[tuple[T_Row]]) -> T_Row | None:
        async with (await self.async_safe_session())() as session:
            result = await session.scalars(sql)
        return cast(T_Row | None, result.first())

    async def add_and_query(self, row, sql: TypedReturnsRows[tuple[T_Row]]) -> T_Row | None:
        async with (await self.async_safe_session())() as session:
            result = await session.scalars(sql)
        return cast(T_Row | None, result.first())

    async def add(self, row):
        async with (await self.async_safe_session())() as session:
            try:
                session.add(row)
                _ = await session.commit()
                _ = await session.refresh(row)
            except Exception:
                _ = await session.rollback()
                raise

    async def add_many(self, rows: Sequence[Base]):
        async with (await self.async_safe_session())() as session:
            try:
                session.add_all(rows)
                _ = await session.commit()
                for row in rows:
                    _ = await session.refresh(row)
            except Exception:
                _ = await session.rollback()
                raise

    async def update_or_add(self, row):
        async with (await self.async_safe_session())() as session:
            try:
                _ = await session.merge(row)
                _ = await session.commit()
                # _ = await session.refresh(row)
            except Exception:
                _ = await session.rollback()
                raise

    async def delete_exist(self, row):
        async with self.async_session() as session:
            await session.delete(row)

    async def delete_many_exist(self, *rows):
        async with self.async_session() as session:
            for row in rows:
                await session.delete(row)
    
    async def create_all(self):
        async with self.engine.begin() as conn:
            for t in Base.__subclasses__():
                if not (await conn.run_sync(self.engine.dialect.has_table, t.__tablename__)):
                    _ = await conn.run_sync(t.metadata.create_all)

    async def drop_all(self):
        async with self.engine.begin() as conn:
            for t in Base.__subclasses__():
                _ = await conn.run_sync(t.metadata.drop_all)

    async def get_exist_tables(self):
        async with self.engine.connect() as conn:
            def use_inspector(conn):
                inspector = inspect(conn)
                return inspector.get_table_names()
            return await conn.run_sync(use_inspector)
