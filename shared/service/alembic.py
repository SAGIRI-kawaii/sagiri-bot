import os
import shutil
from pathlib import Path
from loguru import logger
from sqlalchemy.sql import text
from alembic.config import Config
from alembic.util.exc import CommandError
from alembic.command import revision, upgrade
from alembic.script.revision import ResolutionError
from sqlalchemy.exc import InternalError, ProgrammingError

from kayaku import create
from launart import Launart, Service

from shared.database.model import Base
from shared.models.config import GlobalConfig
from shared.database.interface import Database


async def _alembic():
    if not (Path.cwd() / "alembic").exists():
        logger.info("未检测到alembic目录，进行初始化")
        os.system("alembic init alembic")
        with open(
            Path.cwd() / "resources" / "alembic_env_py_content.txt", "r"
        ) as r:
            alembic_env_py_content = r.read()
        with open(Path.cwd() / "alembic" / "env.py", "w") as w:
            w.write(alembic_env_py_content)
        db_link = create(GlobalConfig).database_setting.db_link
        db_link = (
            db_link.split(":")[0].split("+")[0]
            + ":"
            + ":".join(db_link.split(":")[1:])
        )
        logger.warning(f"尝试自动更改 sqlalchemy.url 为 {db_link}，若出现报错请自行修改")
        alembic_ini_path = Path.cwd() / "alembic.ini"
        lines = alembic_ini_path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            if line.startswith("sqlalchemy.url"):
                lines[i] = line.replace(
                    "driver://user:pass@localhost/dbname", db_link
                )
                break
        alembic_ini_path.write_text("\n".join(lines))
    alembic_version_path = Path.cwd() / "alembic" / "versions"
    if not alembic_version_path.exists():
        alembic_version_path.mkdir()
    cfg = Config(file_="alembic.ini", ini_section="alembic")
    try:
        revision(cfg, message="update", autogenerate=True)
        upgrade(cfg, "head")
    except (CommandError, ResolutionError):
        db = Launart.current().get_interface(Database)
        _ = await db.exec(text("DROP TABLE IF EXISTS alembic_version"))
        shutil.rmtree(alembic_version_path)
        alembic_version_path.mkdir()
        revision(cfg, message="update", autogenerate=True)
        upgrade(cfg, "head")


class AlembicService(Service):
    id = "sagiri.service.alembic"

    @property
    def required(self):
        return set()

    @property
    def stages(self):
        return {"blocking"}

    async def launch(self, _mgr: Launart):
        async with self.stage("blocking"):
            db = Launart.current().get_interface(Database)
            try:
                exist_tables = await db.get_exist_tables()
                async with db.engine.begin() as conn:
                    for t in Base.__subclasses__():
                        if t.__tablename__ not in exist_tables:
                            _ = await conn.run_sync(t.__table__.createm, db.engine)
                _ = await _alembic()
            except (AttributeError, InternalError, ProgrammingError):
                # _ = await db.create_all()
                pass
