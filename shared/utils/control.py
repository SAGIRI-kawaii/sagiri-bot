import ujson
from contextlib import suppress
from sqlalchemy.sql import select
from collections.abc import Mapping
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from launart import Launart
from avilla.core import Message
from avilla.core.selector import Selector
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from shared.database.interface import Database
from shared.models.permission import PermissionLevel
from shared.database.tables import User, UserPermission


class Permission(object):
    """用于管理权限的类，不应被实例化"""

    @classmethod
    async def get(cls, pattern: Mapping[str, str] | Selector):
        if isinstance(pattern, Selector):
            pattern = pattern.pattern
        print(pattern)
        launart = Launart.current()
        db = launart.get_interface(Database)
        pattern = ujson.dumps(dict(pattern))
        res = await db.select_first(select(User).where(User.data_json == pattern).options(selectinload(User.user_permission)))
        if not res:
            with suppress(IntegrityError):
                _ = await db.add(User(data_json=pattern, user_permission=UserPermission()))
        return res.user_permission.level if res else PermissionLevel.DEFAULT.value
        

    @classmethod
    def require(cls, level: int | PermissionLevel):
        async def perm_check(message: Message):
            permission = await cls.get(message.sender)
            if level < permission:
                raise ExecutionStop()
        return Depend(perm_check)


class Blacklist(object):
    """用于管理黑名单的类，不应被实例化"""
        
    @classmethod
    def enable(cls):
        async def blacklist_check(message: Message):
            permission = await Permission.get(message.sender)
            if permission == -1:
                raise ExecutionStop()
        return Depend(blacklist_check)
