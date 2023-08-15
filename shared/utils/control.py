import ujson
from loguru import logger
from datetime import datetime
from collections.abc import Mapping
from sqlalchemy.orm import selectinload

from launart import Launart
from avilla.core import Message, Context
from avilla.core.selector import Selector
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from shared.database.interface import Database
from shared.utils.models import get_scene, get_user
from shared.models.permission import PermissionLevel
from shared.database.tables import User, Scene, UserFunctionCalls


class Permission(object):
    """用于管理权限的类，不应被实例化"""

    @classmethod
    async def get(cls, pattern: Mapping[str, str] | Selector):
        res = await get_user(pattern, selectinload(User.user_permission))
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
                logger.info(f"已屏蔽黑名单用户：{ujson.dumps(dict(message.sender.pattern))}")
                raise ExecutionStop()
        return Depend(blacklist_check)


class Anonymous(object):
    """用于屏蔽qq匿名的类，不应被实例化"""

    @staticmethod
    def block(message_str: str = "不许匿名，你是不是想干坏事？") -> Depend:
        async def judge(ctx: Context, message: Message):
            sender = message.sender
            if sender.land == "qq" and "member" in sender:
                if sender["member"] == 80000000:
                    _ = await ctx.scene.send_message(message_str)
                    raise ExecutionStop()
        return Depend(judge)


class FunctionCall(object):
    """用于用户调用记录的类，不应被实例化"""

    @staticmethod
    def record(func_name: str) -> Depend:
        async def update(message: Message):
            sender = message.sender
            user = await get_user(sender)
            launart = Launart.current()
            db = launart.get_interface(Database)
            await db.add(
                UserFunctionCalls(
                    uid=user.id,
                    time=datetime.now(),
                    func_name=func_name
                )
            )
        return Depend(update)


class Switch(object):
    """用于控制开关的类，不应被实例化"""

    @staticmethod
    def check() -> Depend:
        async def judge(message: Message):
            scene = await get_scene(message.scene, selectinload(Scene.scene_setting))
            if not scene.scene_setting.switch:
                raise ExecutionStop()
        return Depend(judge)