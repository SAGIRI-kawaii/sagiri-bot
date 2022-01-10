import asyncio
import traceback
from functools import wraps
from sqlalchemy import select

from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.utils import get_setting, user_permission_require
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.strategy import QuoteSource, DoNothing
from sagiri_bot.orm.async_orm import UserPermission, Setting, BlackList
from sagiri_bot.frequency_limit_module import GlobalFrequencyLimitDict


def require_permission_level(group: Group, member: Member, level: int):
    def decorate(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if result := await orm.fetchone(
                select(
                    UserPermission.level
                ).where(
                    UserPermission.group_id == group.id and UserPermission.member_id == member.id
                )
            ):
                if result[0] >= level:
                    return await func(*args, **kwargs)
                else:
                    return None
            else:
                await orm.add(UserPermission, {"group_id": group.id, "member_id": member.id, "level": 1})
                if level > 1:
                    return None
                else:
                    return await func(*args, **kwargs)
        return wrapper
    return decorate


def frequency_limit_require_weight_free(weight: int):
    def decorate(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            member_id = -1
            group_id = -1
            for i in args:
                if isinstance(i, Member):
                    member_id = i.id
                if isinstance(i, Group):
                    group_id = i.id
            if member_id == -1 or group_id == -1 or not await get_setting(group_id, Setting.frequency_limit):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            frequency_limit_instance = GlobalFrequencyLimitDict()
            await frequency_limit_instance.add_record(group_id, member_id, weight)
            if frequency_limit_instance.blacklist_judge(group_id, member_id):
                if not frequency_limit_instance.announce_judge(group_id, member_id):
                    await frequency_limit_instance.blacklist_announced(group_id, member_id)
                    return MessageItem(MessageChain.create([Plain(text="检测到大量请求，加入黑名单一小时！")]), QuoteSource())
                else:
                    return MessageItem(MessageChain.create([Plain("")]), DoNothing())
            if frequency_limit_instance.get(group_id, member_id, func.__name__) + weight >= 10:
                return MessageItem(MessageChain.create([Plain(text="超过频率调用限制！")]), QuoteSource())
            else:
                await frequency_limit_instance.update(group_id, weight)
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
        return wrapper
    return decorate


def switch(response_administrator: bool = False):
    def decorate(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            member_id = -1
            group_id = -1
            for i in args:
                if isinstance(i, Member):
                    member_id = i.id
                if isinstance(i, Group):
                    group_id = i.id
            if group_id != -1 and not await get_setting(group_id, Setting.switch):
                if not response_administrator or not await user_permission_require(group_id, member_id, 2):
                    return None
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorate


def blacklist():
    def decorate(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            member_id = -1
            for i in args:
                if isinstance(i, Member):
                    member_id = i.id
            if member_id != -1:
                if await orm.fetchone(
                    select(
                        BlackList.member_id
                    ).where(
                        BlackList.member_id == member_id
                    )
                ):
                    return None
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorate


def debug():
    def decorate(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result
            except:
                return MessageItem(MessageChain.create([Plain(text=traceback.format_exc())]), QuoteSource())
        return wrapper
    return decorate

