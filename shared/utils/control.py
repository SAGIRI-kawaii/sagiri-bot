import time
import random
import contextlib
import sqlalchemy.exc
from asyncio import Lock
from loguru import logger
from sqlalchemy import select
from collections import defaultdict
from typing import DefaultDict, Set, Tuple
from graia.ariadne.message.element import Plain
from typing import Optional, Union, NoReturn, List

from creart import create
from graia.ariadne import Ariadne
from graia.ariadne.model import Member, Group
from graia.ariadne.context import ariadne_ctx
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.builtin.decorators import Depend
from graia.ariadne.model.relationship import MemberPerm

from shared.models.config import GlobalConfig
from shared.models.saya_data import get_saya_data
from shared.models.public_group import PublicGroup
from shared.models.blacklist import GroupBlackList
from shared.models.group_setting import GroupSetting
from shared.utils.permission import user_permission_require
from shared.utils.data_related import update_user_call_count_plus
from shared.models.frequency_limit import GlobalFrequencyLimitDict
from shared.orm import orm, Setting, BlackList, UserPermission, UserCalledCount

group_setting = create(GroupSetting)


class Permission(object):

    """用于管理权限的类，不应被实例化"""

    MASTER = 4
    SUPER_ADMIN = 3
    GROUP_ADMIN = 2
    USER = 1
    BANNED = 0
    GLOBAL_BANNED = -1
    DEFAULT = USER

    @classmethod
    async def get(cls, group: Union[Group, int], member: Union[Member, int]) -> int:
        """
        获取用户的权限
        :param group: 群组实例或QQ群号
        :param member: 用户实例或QQ号
        :return: 等级，整数
        """
        member = member.id if isinstance(member, Member) else member
        group = group.id if isinstance(group, Group) else group
        if result := await orm.fetchone(
            select(UserPermission.level).where(
                UserPermission.group_id == group, UserPermission.member_id == member
            )
        ):
            return result[0]
        with contextlib.suppress(sqlalchemy.exc.IntegrityError):
            await orm.insert_or_ignore(
                UserPermission,
                [UserPermission.group_id == group, UserPermission.member_id == member],
                {"group_id": group, "member_id": member, "level": 1},
            )
        return Permission.DEFAULT

    @classmethod
    def require(cls, level: int = DEFAULT) -> Depend:
        """
        指示需要 `level` 以上等级才能触发，默认为至少 USER 权限
        :param level: 限制等级
        """

        async def perm_check(
            event: GroupMessage, group: Group, source: Source
        ) -> NoReturn:
            if not Permission.DEFAULT <= level <= Permission.MASTER:
                raise ValueError(f"invalid level: {level}")
            member_level = await cls.get(event.sender.group, event.sender)
            if member_level == cls.MASTER:
                pass
            elif member_level < level:
                await ariadne_ctx.get().send_group_message(
                    group,
                    MessageChain(f"权限不足，爬！需要达到等级{level}，你的等级是{member_level}"),
                    quote=source,
                )
                raise ExecutionStop()

        return Depend(perm_check)


class FrequencyLimit(object):
    frequency_limit_dict: Optional[GlobalFrequencyLimitDict] = None

    @classmethod
    def get_frequency_limit_dict(cls):
        if not cls.frequency_limit_dict:
            cls.frequency_limit_dict = create(GlobalFrequencyLimitDict)
        return cls.frequency_limit_dict

    @staticmethod
    def require(
        func_name: str,
        weight: int,
        total_weight: int = 15,
        override_level: int = Permission.MASTER,
        group_admin_override: bool = False,
    ) -> Depend:
        async def limit(event: GroupMessage) -> NoReturn:
            if await Permission.get(event.sender.group, event.sender) >= override_level:
                return
            if group_admin_override and event.sender.permission in {MemberPerm.Administrator, MemberPerm.Owner}:
                return
            member = event.sender.id
            group = event.sender.group.id
            if not await group_setting.get_setting(group, Setting.frequency_limit):
                return
            frequency_limit_instance = create(GlobalFrequencyLimitDict)
            frequency_limit_instance.add_record(group, member, weight)
            if frequency_limit_instance.blacklist_judge(group, member):
                if not frequency_limit_instance.announce_judge(group, member):
                    frequency_limit_instance.blacklist_announced(group, member)
                    await ariadne_ctx.get().send_group_message(
                        group,
                        MessageChain("检测到大量请求，加入黑名单一小时！"),
                        quote=event.message_chain.get_first(Source),
                    )
                raise ExecutionStop()
            if (
                frequency_limit_instance.get(group, member, func_name) + weight
                >= total_weight
            ):
                await ariadne_ctx.get().send_group_message(
                    group,
                    MessageChain("超过频率调用限制！"),
                    quote=event.message_chain.get_first(Source),
                )
                raise ExecutionStop()
            else:
                frequency_limit_instance.update(group, weight)
            return

        return Depend(limit)


class Switch(object):
    @staticmethod
    def enable(response_administrator: bool = False) -> Depend:
        async def switch(event: GroupMessage) -> NoReturn:
            member = event.sender.id
            group = event.sender.group.id
            if not await group_setting.get_setting(group, Setting.switch):
                if response_administrator and await user_permission_require(
                    group, member, 2
                ):
                    return
                raise ExecutionStop()
            return

        return Depend(switch)


class BlackListControl(object):
    @staticmethod
    def enable() -> Depend:
        async def blacklist(event: GroupMessage) -> NoReturn:
            if create(GroupBlackList).blocked(event.sender, event.sender.group):
                raise ExecutionStop()
            return

        return Depend(blacklist)


class Interval(object):

    """用于冷却管理的类，不应被实例化"""

    last_exec: DefaultDict[int, Tuple[int, float]] = defaultdict(lambda: (1, 0.0))
    sent_alert: Set[int] = set()
    lock: Optional[Lock] = None

    @classmethod
    async def get_lock(cls):
        if not cls.lock:
            cls.lock = Lock()
        return cls.lock

    @classmethod
    def require(
        cls,
        suspend_time: float = 10,
        max_exec: int = 1,
        override_level: int = Permission.MASTER,
        silent: bool = False,
    ) -> Depend:
        """
        指示用户每执行 `max_exec` 次后需要至少相隔 `suspend_time` 秒才能再次触发功能
        等级在 `override_level` 以上的可以无视限制
        :param suspend_time: 冷却时间
        :param max_exec: 在再次冷却前可使用次数
        :param override_level: 可超越限制的最小等级
        :param silent: 是否通知
        """

        async def cd_check(event: GroupMessage) -> NoReturn:
            if await Permission.get(event.sender.group, event.sender) >= override_level:
                return
            current = time.time()
            async with (await cls.get_lock()):
                last = cls.last_exec[event.sender.id]
                if current - cls.last_exec[event.sender.id][1] >= suspend_time:
                    cls.last_exec[event.sender.id] = (1, current)
                    if event.sender.id in cls.sent_alert:
                        cls.sent_alert.remove(event.sender.id)
                    return
                elif last[0] < max_exec:
                    cls.last_exec[event.sender.id] = (last[0] + 1, current)
                    if event.sender.id in cls.sent_alert:
                        cls.sent_alert.remove(event.sender.id)
                    return
                if event.sender.id not in cls.sent_alert:
                    if not silent:
                        await ariadne_ctx.get().send_group_message(
                            event.sender.group,
                            MessageChain(
                                [
                                    Plain(
                                        f"冷却还有{last[1] + suspend_time - current:.2f}秒结束，"
                                        f"之后可再执行{max_exec}次"
                                    )
                                ]
                            ),
                            quote=event.message_chain.get_first(Source).id,
                        )
                    cls.sent_alert.add(event.sender.id)
                raise ExecutionStop()

        return Depend(cd_check)


class UserCalledCountControl(object):
    SETU = ("setu", UserCalledCount.setu)
    REAL = ("real", UserCalledCount.real)
    BIZHI = ("bizhi", UserCalledCount.bizhi)
    AT = ("at", UserCalledCount.at)
    SEARCH = ("search", UserCalledCount.search)
    CHAT = ("chat_count", UserCalledCount.chat_count)
    FUNCTIONS = ("functions", UserCalledCount.functions)

    @staticmethod
    def add(data_type: tuple, value: int = 1) -> Depend:
        async def update(event: GroupMessage) -> NoReturn:
            await update_user_call_count_plus(
                event.sender.group, event.sender, data_type[1], data_type[0], value
            )

        return Depend(update)


class Function(object):

    @staticmethod
    def require(
        name: str,
        response_administrator: bool = False,
        log: bool = True,
        notice: bool = False,
    ) -> Optional[Depend]:
        async def judge(app: Ariadne, group: Group, member: Member) -> NoReturn:
            saya_data = get_saya_data()
            if name not in saya_data.switch:
                saya_data.add_saya(name)
            if group.id not in saya_data.switch[name]:
                saya_data.add_group(group)
            if log:
                print(name, saya_data.is_turned_on(name, group))
            if not saya_data.is_turned_on(name, group):
                if saya_data.is_notice_on(name, group) or notice:
                    await app.send_message(
                        group, MessageChain(f"{name}插件已关闭，请联系管理员")
                    )
                raise ExecutionStop()
            if not await group_setting.get_setting(group, Setting.switch):
                if response_administrator and await user_permission_require(
                    group, member, 2
                ):
                    return
                raise ExecutionStop()
            return

        return Depend(judge)


class Config(object):
    sentence: List[MessageChain | str] = ["不配置{config}用个铲铲哦"]
    config: GlobalConfig | None = None

    @classmethod
    def get_config(cls):
        if not cls.config:
            cls.config = create(GlobalConfig)
        return cls.config

    @classmethod
    def require(cls, config: str | None = None):
        async def config_available(app: Ariadne, event: GroupMessage):
            if not config:
                return
            config_instance = cls.get_config()
            paths = config.split(".")
            send_msg = random.choice(cls.sentence)
            msg = MessageChain(send_msg.format(config=config)) if isinstance(send_msg, str) else send_msg
            if len(paths) == 1 and hasattr(config_instance, paths[0]) and not getattr(config_instance, paths[0]):
                await app.send_group_message(event.sender.group, msg)
                raise ExecutionStop()
            current = config_instance
            for path in paths:
                if isinstance(current, GlobalConfig):
                    if hasattr(current, path) and not getattr(current, path):
                        await app.send_group_message(event.sender.group, msg)
                        raise ExecutionStop()
                    elif not hasattr(current, paths[0]):
                        return logger.error(f"不存在的config：{config}")
                    else:
                        current = getattr(current, path)
                        if isinstance(current, str) and current == path:
                            await app.send_group_message(event.sender.group, msg)
                            raise ExecutionStop()
                elif isinstance(current, dict):
                    if path not in current:
                        return logger.error(f"不存在的config：{config}")
                    elif not current.get(path):
                        await app.send_group_message(event.sender.group, msg)
                        raise ExecutionStop()
                    else:
                        current = current.get(path)
                        if isinstance(current, str) and current == path:
                            await app.send_group_message(event.sender.group, msg)
                            raise ExecutionStop()
                else:
                    return

        return Depend(config_available)


class Distribute(object):
    @staticmethod
    def distribute(show_log: bool = False) -> Depend:
        async def judge(app: Ariadne, group: Group, member: Member, source: Source | None) -> NoReturn:
            if member.id in create(GlobalConfig).bot_accounts:
                if show_log:
                    print(app.account, "bot conflict stop")
                raise ExecutionStop()
            p_group = create(PublicGroup)
            if not p_group.account_initialized(app.account):
                if show_log:
                    print(app.account, "not initialized")
                raise ExecutionStop()
            if p_group.need_distribute(group, app.account) and p_group.execution_stop(group, app.account, source):
                if show_log:
                    print(app.account, "stop")
                raise ExecutionStop()
            if show_log:
                print(app.account, "keep")
        return Depend(judge)


class Anonymous(object):
    @staticmethod
    def block(message: str = "不许匿名，你是不是想干坏事？") -> Depend:
        async def judge(app: Ariadne, group: Group, member: Member) -> NoReturn:
            if member.id == 80000000:
                await app.send_group_message(group, MessageChain(message))
                raise ExecutionStop()
        return Depend(judge)
