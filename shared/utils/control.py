import ujson
from loguru import logger
from datetime import datetime
from collections.abc import Mapping
from sqlalchemy.orm import selectinload

from creart import it
from kayaku import create
from avilla.core import Message, Context
from avilla.core.selector import Selector
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from shared.models import PluginData
from shared.database import get_interface
from shared.utils.models import get_scene, get_user
from shared.models.permission import PermissionLevel
from shared.services.distribute import DistributeData
from shared.database.tables import User, Scene, UserFunctionCalls


class Permission(object):
    """用于管理权限的类，不应被实例化"""

    @classmethod
    async def get(cls, pattern: Mapping[str, str] | Selector) -> int:
        res = await get_user(pattern, selectinload(User.user_permission))
        return res.user_permission.level if res else PermissionLevel.DEFAULT.value
        
    @classmethod
    def require(cls, level: int | PermissionLevel, notice: bool = True):
        if isinstance(level, PermissionLevel):
            level = level.value
        async def perm_check(ctx: Context, message: Message):
            permission = await cls.get(message.sender)
            if level > permission:
                if notice:
                    _ = await ctx.scene.send_message(f"权限不足，需要权限级{level}，你的权限为{permission}")
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
            await get_interface().add(
                UserFunctionCalls(
                    uid=user.id,
                    time=datetime.now(),
                    func_name=func_name
                )
            )
        return Depend(update)


class SceneSwitch(object):
    """用于控制场景响应开关的类，不应被实例化"""

    @staticmethod
    def check() -> Depend:
        async def judge(message: Message):
            scene = await get_scene(message.scene, selectinload(Scene.scene_setting))
            if not scene.scene_setting.switch:
                raise ExecutionStop()
        return Depend(judge)


class Function(object):
    """用于控制单模块模块开关的类，不应被实例化"""

    @staticmethod
    def require(
        name: str,
        *,
        response_administrator: bool = False,
        notice: bool = False,
    ) -> Depend:
        async def judge(ctx: Context, message: Message):
            plugin_data = create(PluginData)
            switch = plugin_data.is_on(name, message)
            logger.debug(f"log from decorator Function: module <{name}>'s switch: {switch}")
            if not switch and (notice or plugin_data.is_notice_on(name, message)):
                _ = await ctx.scene.send_message(f"模组<{name}>已关闭！请联系机器人管理员！")
                raise ExecutionStop()
        return Depend(judge)


class Distribute(object):
    """用于控制负载均衡的类，不应被实例化"""
    @staticmethod
    def distribute(require_admin: bool = False, show_log: bool = False) -> Depend:
        async def judge(ctx: Context, message: Message):
            base_account = ctx.account
            land = base_account.route["land"]
            account = base_account.route["account"]

            # TODO: 添加bot冲突检测，检测已加载account

            distribute_data = it(DistributeData)
            if not distribute_data.account_initialized(account):
                _ = await distribute_data.add_account(base_account)
                if show_log:
                    logger.warning(f"{account} not initialized")
                raise ExecutionStop()
            if all([
                distribute_data.need_distribute(land, message.scene),
                await distribute_data.execution_stop(base_account, message.scene, message)
            ]):
                if show_log:
                    logger.debug(f"{account} stop")
                raise ExecutionStop()
            if show_log:
                logger.debug(f"{account} keep")
        return Depend(judge)
