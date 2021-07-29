import asyncio
import traceback
from loguru import logger
from functools import wraps
from sqlalchemy import select

from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.ORM.AsyncORM import orm
from SAGIRIBOT.utils import get_setting
from SAGIRIBOT.ORM.AsyncORM import UserPermission, Setting
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.Core.Exceptions import FrequencyLimitExceeded
from SAGIRIBOT.Core.Exceptions import FrequencyLimitExceededDoNothing
from SAGIRIBOT.frequency_limit_module import GlobalFrequencyLimitDict
from SAGIRIBOT.Core.Exceptions import FrequencyLimitExceededAddBlackList
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource, DoNoting


def require_permission_level(group: Group, member: Member, level: int):
    def decorate(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # print(group.name, member.name)
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
                    # print("等级不够呢~")
                    return None
            else:
                await orm.add(UserPermission, {"group_id": group.id, "member_id": member.id, "level": 1})
                if level > 1:
                    # print("等级不够呢~")
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
                    return MessageItem(MessageChain.create([Plain(text="检测到大量请求，加入黑名单一小时！")]), QuoteSource(GroupStrategy()))
                else:
                    return MessageItem(MessageChain.create([Plain("")]), DoNoting(GroupStrategy()))
            if frequency_limit_instance.get(group_id, member_id, func.__name__) + weight >= 10:
                return MessageItem(MessageChain.create([Plain(text="超过频率调用限制！")]), QuoteSource(GroupStrategy()))
            else:
                await frequency_limit_instance.update(group_id, weight)
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
        return wrapper
    return decorate
