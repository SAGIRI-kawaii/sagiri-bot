import traceback
from enum import Enum
from typing import Union
from loguru import logger
from sqlalchemy import select

from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, Member

from .commands import *
from sagiri_bot.orm.async_orm import orm
from sagiri_bot.utils import user_permission_require
from sagiri_bot.message_sender.message_sender import MessageItem
from sagiri_bot.message_sender.strategy import Normal, QuoteSource
from sagiri_bot.orm.async_orm import Setting, UserPermission, BlackList


class BlackListType(Enum):
    pass


def camel_to_underscore(s: str) -> str:
    result = s[0]
    for i in range(1, len(s)):
        if s[i].isupper() and not s[i - 1].isupper():
            result += '_'
            result += s[i]
        elif s[i].isupper() and s[i - 1].isupper() and s[i + 1].islower():
            result += '_'
            result += s[i]
        else:
            result += s[i]
    return result.lower()


async def execute_setting_update(group: Group, member: Member, command: str) -> MessageItem:
    """
        setting -set setu=True real=True
        多命令执行
    """
    commands = command[13:].split(" ")
    error_commands = []
    success_commands = []
    for command in commands:
        try:
            command = command.strip()    # .replace("-", "")
            if not command:
                continue
            func, value = command.split("=")
            func = camel_to_underscore(func)
            value = (True if value == "True" else False) if value in ["True", "False"] else value
            if func in command_index.keys():
                if command_index[func].is_valid(value):
                    """ update """
                    if await user_permission_require(group, member, command_index[func].level):
                        try:
                            await orm.insert_or_update(Setting, [Setting.group_id == group.id], {func: value})
                            success_commands.append(f"{func} -> {value}")
                        except Exception as e:
                            error_commands.append((command, str(e)))
                            logger.error(traceback.format_exc())
                    else:
                        error_commands.append((command, f"权限不足，要求权限等级{command_index[func].level}"))
                else:
                    error_commands.append((f"{func} -> {value}", f"期望值：{'，'.join([str(valid_value) for valid_value in command_index[func].valid_values])}"))
            else:
                error_commands.append((command, "未找到此命令"))
        except ValueError:
            error_commands.append((command, "格式非法！应为 func=value"))
    response_text = f"共解析{len(commands)}条命令，\n其中{len(success_commands)}条执行成功，{len(error_commands)}条失败"
    if success_commands:
        response_text += "\n\n成功命令："
        for i in success_commands:
            response_text += f"\n{i}"
    if error_commands:
        response_text += "\n\n失败命令："
        for i in error_commands:
            response_text += f"\n{i[0]} | {i[1]}"
    return MessageItem(MessageChain.create([Plain(text=response_text)]), Normal())


async def execute_grant_permission(group: Group, member: Member, message_text: str) -> MessageItem:
    if await user_permission_require(group, member, 3):
        message_text = message_text[13:]
        try:
            target, level = message_text.split(" ")
        except ValueError:
            return MessageItem(MessageChain.create([Plain("格式错误！使用方法：user -grant @user level[1-3]")]), QuoteSource())
        target = int(target)
        if level.isdigit():
            level = int(level)
            if member.id == target and level != 4 and await user_permission_require(group, member, 4):
                return MessageItem(MessageChain.create([Plain(text="怎么有master想给自己改权限欸？纱雾很关心你呢~快去脑科看看吧！")]), QuoteSource())
            if 1 <= level <= 2:
                if result := await orm.fetchone(select(UserPermission.level).where(UserPermission.group_id == group.id, UserPermission.member_id == target)):
                    if result[0] == 4:
                        if await user_permission_require(group, member, 4):
                            return MessageItem(MessageChain.create([Plain(text="就算是master也不能修改master哦！（怎么会有两个master，怪耶）")]),QuoteSource())
                        else:
                            return MessageItem(MessageChain.create([Plain(text="master level 不可更改！若想进行修改请直接修改数据库！")]), QuoteSource())
                    if result[0] == 3:
                        if await user_permission_require(group, member, 4):
                            return await grant_permission_process(group.id, target, level)
                        else:
                            return MessageItem(MessageChain.create([Plain(text="权限不足，你必须达到权限等级4(master level)才可对超级管理员权限进行修改！")]), QuoteSource())
                    else:
                        return await grant_permission_process(group.id, target, level)
                else:
                    return await grant_permission_process(group.id, target, level)
            elif level == 3:
                if await user_permission_require(group, member, 4):
                    return await grant_permission_process(group.id, target, level)
                else:
                    return MessageItem(MessageChain.create([Plain(text="格式错误！权限不足，你必须达到权限等级4(master level)才可对超级管理员进行授权！")]), Normal())
            else:
                return MessageItem(MessageChain.create([Plain("level值非法！合法level值：1-3\n1: user\n2: administrator\n3: super administrator")]), QuoteSource())
        else:
            return MessageItem(MessageChain.create([Plain("格式错误！使用方法：user -grant @user level[1-3]")]), QuoteSource())
    else:
        return MessageItem(MessageChain.create([Plain(text="权限不足，爬!")]), QuoteSource())


async def grant_permission_process(group_id: int, member_id: int, new_level: int) -> MessageItem:
    if await grant_permission(group_id, member_id, new_level):
        return MessageItem(MessageChain.create([Plain(text=f"修改成功！\n{member_id} permission level: {new_level}")]), Normal())
    else:
        return MessageItem(MessageChain.create([Plain(text="出现错误，请查看日志！")]), QuoteSource())


async def grant_permission(group_id: int, member_id: int, new_level: int) -> bool:
    try:
        await orm.insert_or_update(
            UserPermission,
            [UserPermission.group_id == group_id, UserPermission.member_id == member_id],
            {"group_id": group_id, "member_id": member_id, "level": new_level}
        )
        return True
    except Exception:
        logger.error(traceback.format_exc())
        return False


async def execute_blacklist_append(member_id: int, group: Group, operator: Member) -> MessageItem:
    try:
        if not await user_permission_require(group, operator, 2):
            return MessageItem(MessageChain.create([Plain(text="权限不足，爬！")]), QuoteSource())
        if await check_admin(member_id, group):
            return MessageItem(
                MessageChain.create([Plain(text="用户权限等级>=2的用户无法被加入黑名单！若想将其加入黑名单请先将其权限等级将为1！")]),
                QuoteSource()
            )
        if await orm.fetchone(
            select(
                BlackList.member_id, BlackList.group_id
            ).where(
                BlackList.member_id == member_id,
                BlackList.group_id == group.id
            )
        ):
            return MessageItem(MessageChain.create([Plain(text=f"{member_id} 已经在本群黑名单中了！")]), QuoteSource())
        await orm.insert_or_ignore(
            BlackList,
            [BlackList.member_id == member_id, BlackList.group_id == group.id],
            {"member_id": member_id, "group_id": group.id}
        )
        return MessageItem(MessageChain.create([Plain(text=f"{member_id} 添加本群黑名单成功")]), QuoteSource())
    except Exception as e:
        logger.error(traceback.format_exc())
        return MessageItem(MessageChain.create([Plain(text=str(e))]), QuoteSource())


async def execute_blacklist_remove(member_id: int, group: Group, operator: Member) -> MessageItem:
    try:
        if not await user_permission_require(group, operator, 2):
            return MessageItem(MessageChain.create([Plain(text="权限不足，爬！")]), QuoteSource())
        if not await orm.fetchone(
            select(
                BlackList.member_id, BlackList.group_id
            ).where(
                BlackList.member_id == member_id,
                BlackList.group_id == group.id
            )
        ):
            return MessageItem(MessageChain.create([Plain(text=f"{member_id} 不在本群黑名单中！")]), QuoteSource())
        await orm.delete(
            BlackList,
            [BlackList.member_id == member_id, BlackList.group_id == group.id]
        )
        return MessageItem(MessageChain.create([Plain(text=f"{member_id} 移除本群黑名单成功")]), QuoteSource())
    except Exception as e:
        logger.error(traceback.format_exc())
        return MessageItem(MessageChain.create([Plain(text=str(e))]), QuoteSource())


async def check_admin(member: Union[int, Member], group: Union[int, Group]) -> bool:
    if isinstance(member, Member):
        member = member.id
    if isinstance(group, Group):
        group = group.id
    if res := await orm.fetchone(
        select(
            UserPermission.level
        ).where(
            UserPermission.group_id == group,
            UserPermission.member_id == member
        )
    ):
        return res[0] >= 2
    else:
        return False

