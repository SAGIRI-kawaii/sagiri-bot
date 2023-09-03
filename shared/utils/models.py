import ujson
from contextlib import suppress
from sqlalchemy.sql import select
from collections.abc import Mapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.base import ExecutableOption

from avilla.core.selector import Selector
from shared.database.tables import User, UserPermission, Scene, SceneSetting

from shared.database import get_interface


def selector2pattern(selector: Mapping[str, str] | Selector) -> str:
    if isinstance(selector, Selector):
        selector = selector.pattern
    return ujson.dumps(dict(selector))


async def get_model(model: User | Scene, selector: Mapping[str, str] | Selector, *sql_options: ExecutableOption, **add_options) -> User | Scene:
    db = get_interface()
    pattern = selector2pattern(selector)
    sql = select(model).where(model.data_json == pattern)
    if sql_options:
        sql = sql.options(*sql_options)
    res = await db.select_first(sql)
    if not res:
        with suppress(IntegrityError):
            _ = await db.add(model(data_json=pattern, **add_options))
        res = await db.select_first(sql)
    return res


async def get_user(sender: Mapping[str, str] | Selector, *sql_options: ExecutableOption, **add_options) -> User:
    return await get_model(User, sender, *sql_options, user_permission=UserPermission(), **add_options)


async def get_scene(scene: Mapping[str, str] | Selector, *sql_options: ExecutableOption, **add_options) -> Scene:
    return await get_model(Scene, scene, *sql_options, scene_setting=SceneSetting(), **add_options)
