from loguru import logger
from sqlalchemy.exc import InternalError, ProgrammingError

from creart import it
from launart import Launart, Service

from shared.orm import AsyncORM


class SagiriDBService(Service):
    id = "sagiri.service.db"

    @property
    def required(self):
        return set()

    @property
    def stages(self):
        return {"preparing"}

    async def launch(self, _mgr: Launart):
        async with self.stage("preparing"):
            orm = it(AsyncORM)
            try:
                await orm.init_check()
            except (AttributeError, InternalError, ProgrammingError):
                await orm.create_all()
            logger.success("数据库初始化完成")
