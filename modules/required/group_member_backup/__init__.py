from sqlalchemy import select

from creart import create
from graia.ariadne import Ariadne
from graia.saya import Channel
from graia.ariadne.message.element import Source
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, ArgumentMatch, ArgResult

from shared.models.config import GlobalConfig
from shared.orm import orm, GroupMembersBackup
from shared.utils.type import parse_match_type
from shared.utils.module_related import get_command
from shared.utils.control import (
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute,
    Permission
)

channel = Channel.current()

channel.name("GroupMembersBackup")
channel.author("SAGIRI-kawaii")
channel.description("一个备份群成员的插件")

config = create(GlobalConfig)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                # ArgumentMatch("-s", "-save", action="store_true", optional=True) @ "save",
                ArgumentMatch("-s", "-show", action="store_true", optional=True) @ "show",
                ArgumentMatch("-g", "-group", optional=True) @ "show_group",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
            Permission.require(Permission.GROUP_ADMIN)
        ]
    )
)
async def group_member_backup(app: Ariadne, group: Group, source: Source, show: ArgResult, show_group: ArgResult):
    if show.matched:
        if not show_group.matched:
            return await app.send_message(group, "请使用 -g=qq群号 来给出要查询的群号！", quote=source)
        if show_group := parse_match_type(show_group, int, 0):
            if res := await orm.fetchone(
                select(
                    GroupMembersBackup.group_id,
                    GroupMembersBackup.group_name,
                    GroupMembersBackup.members
                ).where(
                    GroupMembersBackup.group_id == show_group
                )
            ):
                return await app.send_message(
                    group, f"查询到群组 <{res[1]}>({res[0]}) 有以下群成员：{res[2].replace(',', ', ').replace('|', ' | ')}"
                )
            else:
                return await app.send_message(group, f"未找到群 <{show_group}> 的数据！")
        else:
            return await app.send_message(group, f"群号<{show_group}>格式错误！", quote=source)
    members = await app.get_member_list(group)
    _ = await orm.insert_or_update(
        GroupMembersBackup,
        [GroupMembersBackup.group_id == group.id],
        {"group_id": group.id, "group_name": group.name, "members": ",".join([f"{m.name}|{m.id}" for m in members])}
    )
    await app.send_message(group, f"群组 <{group.name}({group.id})> 备份完成", quote=source)
