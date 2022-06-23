import time
from asyncio import Lock
from sqlalchemy import select
from collections import defaultdict
from typing import DefaultDict, Set, Tuple
from typing import Optional, Union, NoReturn
from graia.ariadne.message.element import Plain

from graia.ariadne.model import Member, Group
from graia.ariadne.context import ariadne_ctx
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.builtin.decorators import Depend

from sagiri_bot.orm.async_orm import UserCalledCount
from sagiri_bot.frequency_limit_module import GlobalFrequencyLimitDict
from sagiri_bot.orm.async_orm import orm, Setting, BlackList, UserPermission
from sagiri_bot.handler.required_module.saya_manager.utils import saya_data, SayaData
from sagiri_bot.utils import group_setting, user_permission_require, update_user_call_count_plus


class Permission(object):

    """ 用于管理权限的类，不应被实例化 """

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
            select(
                UserPermission.level
            ).where(
                UserPermission.group_id == group,
                UserPermission.member_id == member
            )
        ):
            return result[0]
        else:
            await orm.insert_or_ignore(
                UserPermission,
                [UserPermission.group_id == group, UserPermission.member_id == member],
                {"group_id": group, "member_id": member, "level": 1}
            )
            return Permission.DEFAULT

    @classmethod
    def require(cls, level: int = DEFAULT) -> Depend:
        """
        指示需要 `level` 以上等级才能触发，默认为至少 USER 权限
        :param level: 限制等级
        """

        async def perm_check(event: GroupMessage, group: Group) -> NoReturn:
            if not Permission.DEFAULT <= level <= Permission.MASTER:
                raise ValueError(f"invalid level: {level}")
            member_level = await cls.get(event.sender.group, event.sender)
            if member_level == cls.MASTER:
                pass
            elif member_level < level:
                await ariadne_ctx.get().sendGroupMessage(
                    group,
                    MessageChain(f"权限不足，爬！需要达到等级{level}，你的等级是{member_level}"),
                    quote=event.messageChain.getFirst(Source)
                )
                raise ExecutionStop()

        return Depend(perm_check)


class FrequencyLimit(object):
    frequency_limit_dict: Optional[GlobalFrequencyLimitDict] = None

    @classmethod
    async def get_frequency_limit_dict(cls):
        if not cls.frequency_limit_dict:
            cls.frequency_limit_dict = GlobalFrequencyLimitDict()
        return cls.frequency_limit_dict

    @staticmethod
    def require(
            func_name: str,
            weight: int,
            total_weight: int = 10,
            override_level: int = Permission.MASTER,
            group_admin_override: bool = False
    ) -> Depend:
        async def limit(event: GroupMessage) -> NoReturn:
            if await Permission.get(event.sender.group, event.sender) >= override_level:
                return
            member = event.sender.id
            group = event.sender.group.id
            if not await group_setting.get_setting(group, Setting.frequency_limit):
                return
            frequency_limit_instance = await FrequencyLimit.get_frequency_limit_dict()
            await frequency_limit_instance.add_record(group, member, weight)
            if frequency_limit_instance.blacklist_judge(group, member):
                if not frequency_limit_instance.announce_judge(group, member):
                    await frequency_limit_instance.blacklist_announced(group, member)
                    await ariadne_ctx.get().sendGroupMessage(
                        group, MessageChain("检测到大量请求，加入黑名单一小时！"), quote=event.messageChain.getFirst(Source)
                    )
                raise ExecutionStop()
            if frequency_limit_instance.get(group, member, func_name) + weight >= total_weight:
                await ariadne_ctx.get().sendGroupMessage(
                    group, MessageChain("超过频率调用限制！"), quote=event.messageChain.getFirst(Source)
                )
                raise ExecutionStop()
            else:
                await frequency_limit_instance.update(group, weight)
            return

        return Depend(limit)


class Switch(object):
    @staticmethod
    def enable(response_administrator: bool = False) -> Depend:
        async def switch(event: GroupMessage) -> NoReturn:
            member = event.sender.id
            group = event.sender.group.id
            if not await group_setting.get_setting(group, Setting.switch):
                if response_administrator and await user_permission_require(group, member, 2):
                    return
                raise ExecutionStop()
            return

        return Depend(switch)


class BlackListControl(object):
    @staticmethod
    def enable() -> Depend:
        async def blacklist(event: GroupMessage) -> NoReturn:
            member = event.sender.id
            group = event.sender.group.id
            if await orm.fetchone(
                    select(
                        BlackList.member_id
                    ).where(
                        BlackList.member_id == member,
                        BlackList.group_id == group
                    )
            ) or await orm.fetchone(
                select(
                    BlackList.member_id
                ).where(
                    BlackList.member_id == member,
                    BlackList.is_global is True
                )
            ):
                raise ExecutionStop()
            return

        return Depend(blacklist)


class Interval(object):

    """ 用于冷却管理的类，不应被实例化 """

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
                        await ariadne_ctx.get().sendGroupMessage(
                            event.sender.group,
                            MessageChain.create(
                                [
                                    Plain(
                                        f"冷却还有{last[1] + suspend_time - current:.2f}秒结束，"
                                        f"之后可再执行{max_exec}次"
                                    )
                                ]
                            ),
                            quote=event.messageChain.getFirst(Source).id,
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
            await update_user_call_count_plus(event.sender.group, event.sender, data_type[1], data_type[0], value)
        return Depend(update)


class Function(object):
    saya_data: SayaData

    @classmethod
    def get_saya_data(cls):
        if not cls.saya_data:
            cls.saya_data = saya_data
        return cls.saya_data

    @classmethod
    def require(
        cls, name: str, response_administrator: bool = False, log: bool = True, notice: bool = False
    ) -> Optional[Depend]:
        async def judge(event: GroupMessage) -> NoReturn:
            member = event.sender
            group = member.group
            if name not in saya_data.switch:
                saya_data.add_saya(name)
            if group.id not in saya_data.switch[name]:
                saya_data.add_group(group)
            if log:
                print(name, saya_data.is_turned_on(name, group))
            if not saya_data.is_turned_on(name, group):
                if saya_data.is_notice_on(name, group) or notice:
                    await ariadne_ctx.get().sendMessage(
                        group, MessageChain(f"{name}插件已关闭，请联系管理员")
                    )
                raise ExecutionStop()
            if not await group_setting.get_setting(group, Setting.switch):
                if response_administrator and await user_permission_require(group, member, 2):
                    return
                raise ExecutionStop()
            return

        return Depend(judge)
