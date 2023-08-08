from typing import Any, Literal

from launart import Service
from loguru import logger

from shared.database.interface import Database
from shared.database.manager import DatabaseManager


class DatabaseService(Service):
    id: str = "sagiri.service.database"
    db: DatabaseManager
    supported_interface_types: set[Any] = {Database}

    def __init__(self, url: str = "sqlite+aiosqlite:///data.db") -> None:
        self.db = DatabaseManager(url)
        super().__init__()

    def get_interface(self, typ: type[Database]) -> Database:
        return Database(self.db)

    @property
    def required(self) -> set[str]:
        return set()

    @property
    def stages(self) -> set[Literal["preparing", "blocking", "cleanup"]]:
        return {"preparing", "cleanup"}

    async def launch(self, _):
        logger.info("Initializing database...")
        await self.db.initialize()
        logger.success("Database initialized!")

        async with self.stage("preparing"):
            ...

        async with self.stage("cleanup"):
            await self.db.stop()
