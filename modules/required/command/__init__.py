from pathlib import Path

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import ArgResult, ArgumentMatch, WildcardMatch, RegexResult

from shared.utils.files import load_json
from .utils import get_targets, target_valid
from shared.utils.type import parse_match_type
from shared.models.blacklist import GroupBlackList
from shared.models.group_setting import GroupSetting
from shared.models.permission import GroupPermission
from shared.utils.module_related import get_command_by_metadata
from shared.utils.control import (
    Function,
    BlackListControl,
    Distribute,
    Permission
)

saya = Saya.current()
channel = Channel.current()

channel.name("Command")
channel.author("SAGIRI-kawaii")
channel.description("一个执行管理命令的插件")

valid_value = load_json(Path(__file__).parent / "valid_value.json")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command_by_metadata(__file__, "setting"),
                ArgumentMatch("-set", "-set", "-s", action="store_true", optional=True) @ "for_group",
                ArgumentMatch("--set-all", "-all", "-a", "-g", "-global", action="store_true", optional=True) @ "for_all",
                WildcardMatch() @ "commands"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module),
            BlackListControl.enable(),
            Permission.require(Permission.GROUP_ADMIN)
        ],
    )
)
async def setting(app: Ariadne, group: Group, for_group: ArgResult, for_all: ArgResult, commands: RegexResult):
    if not for_all.matched and not for_group.matched:
        return
    group_setting = create(GroupSetting)
    error_commands = []
    success_commands = []
    commands = commands.result.display.strip().split(" ")
    for command in commands:
        command = command.strip()
        if not command:
            continue
        try:
            func, value = command.split("=")
            if func not in valid_value:
                error_commands.append((command, "未找到此命令"))
                continue
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            if value not in valid_value[func]:
                error_commands.append((
                    f"{func} -> {value}",
                    f"期望值：{'，'.join([str(v) for v in valid_value[func]])}",
                ))
            if for_all.matched:
                _ = await group_setting.modify_setting(func, value)
            else:
                _ = await group_setting.modify_setting(func, value, group)
            success_commands.append(f"{func} -> {value}")
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
    await app.send_message(group, response_text)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command_by_metadata(__file__, "blacklist"),
                ArgumentMatch("-add", action="store_true", optional=True) @ "add",
                ArgumentMatch("-remove", "-r", action="store_true", optional=True) @ "remove",
                ArgumentMatch("-clear", "-c", action="store_true", optional=True) @ "clear",
                ArgumentMatch("-all", "-a", "-global", "-g", action="store_true", optional=True) @ "is_global",
                WildcardMatch() @ "targets"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module),
            BlackListControl.enable(),
            Permission.require(Permission.SUPER_ADMIN)
        ],
    )
)
async def blacklist(
    app: Ariadne,
    group: Group,
    add: ArgResult,
    remove: ArgResult,
    clear: ArgResult,
    is_global: ArgResult,
    targets: RegexResult
):
    if not any([
        add.matched,
        remove.matched,
        clear.matched
    ]):
        return
    error_targets = []
    success_targets = []
    group_blacklist = create(GroupBlackList)
    targets = get_targets(targets.result)
    if add.matched:
        if is_global.matched:
            for target in targets:
                _ = await group_blacklist.add(target, -1, True)
        else:
            for target in targets:
                if await target_valid(target, group):
                    _ = await group_blacklist.add(target, group)
                    success_targets.append(target)
                else:
                    error_targets.append((target, "目标不存在于群组中"))
    elif remove.matched:
        if is_global.matched:
            for target in targets:
                _ = await group_blacklist.remove(target, -1, True)
        else:
            for target in targets:
                if await target_valid(target, group):
                    _ = await group_blacklist.remove(target, group)
                    success_targets.append(target)
                else:
                    error_targets.append((target, "目标不存在于群组中"))
    elif clear.matched:
        for target in targets:
            _ = await group_blacklist.clear(target)
            success_targets.append(target)
    response_text = f"共解析{len(targets)}个目标，\n其中{len(success_targets)}个执行成功，{len(error_targets)}个失败"
    if success_targets:
        response_text += "\n\n成功目标："
        for i in success_targets:
            response_text += f"\n{i}"
    if error_targets:
        response_text += "\n\n失败目标："
        for i in error_targets:
            response_text += f"\n{i[0]} | {i[1]}"
    await app.send_message(group, response_text)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command_by_metadata(__file__, "user"),
                ArgumentMatch("-grant", action="store_true") @ "grant",
                ArgumentMatch("-all", "-a", "-global", "-g", action="store_true", optional=True) @ "is_global",
                ArgumentMatch("-l", "-level") @ "level",
                WildcardMatch() @ "targets"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module),
            BlackListControl.enable(),
            Permission.require(Permission.SUPER_ADMIN)
        ],
    )
)
async def user_grant(
    app: Ariadne,
    group: Group,
    member: Member,
    grant: ArgResult,
    level: ArgResult,
    is_global: ArgResult,
    targets: RegexResult
):
    if grant.matched:
        level = parse_match_type(level, int, 0)
        if not 1 <= level <= 3:
            return await app.send_message(group, "level 必须在 1-3 之间！")
        permission = create(GroupPermission)
        operator_level = await permission.get_permission(group, member)
        if level >= operator_level:
            return await app.send_message(group, "你不能将其他人权限提升至与自身等级相等！")
        targets = get_targets(targets.result)
        error_targets = []
        for target in targets:
            if operator_level <= await permission.get_permission(group, target):
                error_targets.append((target, "target's level >= your level!"))
            else:
                await permission.update(group, target, level, is_global.matched)
        response_text = f"共解析{len(targets)}个目标，\n其中{len(targets) - len(error_targets)}个执行成功，{len(error_targets)}个失败"
        if error_targets:
            response_text += "\n\n失败目标："
            for i in error_targets:
                response_text += f"\n{i[0]} | {i[1]}"
        await app.send_message(group, response_text)
