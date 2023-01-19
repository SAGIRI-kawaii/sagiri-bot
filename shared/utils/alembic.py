from sqlalchemy.exc import InternalError, ProgrammingError

from creart import create
from launart import Launchable, Launart

from core import Sagiri
from shared.orm import orm


class AlembicService(Launchable):
    id = "sagiri.core.alembic"

    @property
    def required(self):
        return set()

    @property
    def stages(self):
        return {"preparing"}

    async def launch(self, _mgr: Launart):
        async with self.stage("preparing"):
            try:
                _ = await orm.init_check()
                core = create(Sagiri)
                _ = await core.alembic()
            except (AttributeError, InternalError, ProgrammingError):
                _ = await orm.create_all()
