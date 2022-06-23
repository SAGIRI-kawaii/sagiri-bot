import re
from sqlalchemy import select
from typing import Union, List

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source, At
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult, UnionMatch, WildcardMatch

from sagiri_bot.orm.async_orm import orm, GroupTeam
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl, Permission

saya = Saya.current()
channel = Channel.current()

channel.name("GroupTeam")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个可以将群内组员分为小组进行呼叫的插件\n"
    "发送 `群小组/group_team 添加分组/创建分组/create <小组名> <@要添加的组员>` 即可创建分组\n"
    "发送 `群小组/group_team 删除分组/解散分组/delete <小组名>` 即可删除分组\n"
    "发送 `群小组/group_team 添加成员/add <小组名> <@要添加的组员>` 即可在分组中添加成员\n"
    "发送 `群小组/group_team 移除成员/删除成员/remove <小组名> <@要移除的组员>` 即可在分组中移除成员\n"
    "发送 `群小组/group_team 通知/呼叫/notice/call <小组名> <要发送的信息>` 即可对小组内成员发送消息\n"
    "发送 `群小组/group_team 列出/显示/列表/show/list` 即可查看所在群组中所有小组\n"
    "发送 `群小组/group_team 列出/显示/列表/show/list <小组名>` 即可查看小组内组员"
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("群小组", "group_team"),
                UnionMatch("添加分组", "创建分组", "create"),
                RegexMatch(r"[\S]+") @ "team_name",
                WildcardMatch() @ "teammates"
            ])
        ],
        decorators=[
            FrequencyLimit.require("group_team_new_team", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            Permission.require(Permission.GROUP_ADMIN),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def group_team_new_team(
    app: Ariadne, group: Group, member: Member, source: Source, team_name: RegexResult, teammates: RegexResult
):
    team_name = team_name.result.asDisplay().strip()
    teammates = teammates.result.get(At)
    if await team_exists(group, team_name):
        return await app.sendGroupMessage(
            group,
            MessageChain(f"小组 {team_name} 已存在！请更换名称或使用 `群小组 添加成员 {team_name} <@要加入的成员>` 命令添加成员！"),
            quote=source
        )
    teammates = "|".join(str(teammate.target) for teammate in teammates)
    await orm.insert_or_ignore(
        GroupTeam,
        [GroupTeam.group_id == group.id, GroupTeam.name == team_name],
        {"creator": member.id, "group_id": group.id, "name": team_name, "teammates": teammates}
    )
    await app.sendGroupMessage(group, MessageChain(f"已成功创建小组 <{team_name}>"), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("群小组", "group_team"),
                UnionMatch("删除分组", "解散分组", "delete"),
                RegexMatch(r"[\S]+") @ "team_name"
            ])
        ],
        decorators=[
            FrequencyLimit.require("group_team", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            Permission.require(Permission.GROUP_ADMIN),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def group_team_delete_team(
    app: Ariadne, group: Group, source: Source, team_name: RegexResult
):
    team_name = team_name.result.asDisplay().strip()
    if not await team_exists(group, team_name):
        return await app.sendGroupMessage(
            group,
            MessageChain(f"小组 {team_name} 不存在！请检查名称！"),
            quote=source
        )
    await orm.delete(
        GroupTeam, [GroupTeam.group_id == group.id, GroupTeam.name == team_name]
    )
    await app.sendGroupMessage(group, MessageChain(f"已成功删除小组 <{team_name}>"), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("群小组", "group_team"),
                UnionMatch("添加成员", "add", "移除成员", "删除成员", "remove") @ "op",
                RegexMatch(r"[\S]+") @ "team_name",
                WildcardMatch() @ "teammates"
            ])
        ],
        decorators=[
            FrequencyLimit.require("group_team_modify_teammate", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            Permission.require(Permission.GROUP_ADMIN),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def group_team_modify_teammate(
    app: Ariadne, group: Group, source: Source, op: RegexResult, team_name: RegexResult, teammates: RegexResult
):
    team_name = team_name.result.asDisplay().strip()
    new_teammates = teammates.result.get(At)
    if not await team_exists(group, team_name):
        return await app.sendGroupMessage(
            group,
            MessageChain(f"小组 {team_name} 不存在！请更换名称或使用 `群小组 创建分组 {team_name} <@要加入的成员>` 命令新建小组！"),
            quote=source
        )
    team = await get_team(group, team_name)
    teammates = list(map(int, team[3].split('|')))
    modify_count = 0
    op = op.result.asDisplay().strip()
    if op in ("添加成员", "add"):
        teammate_exists = []
        for teammate in new_teammates:
            if teammate.target not in teammates:
                modify_count += 1
                teammates.append(teammate.target)
            else:
                teammate_exists.append(teammate.target)
    else:
        teammate_not_exists = []
        for teammate in new_teammates:
            if teammate.target in teammates:
                modify_count += 1
                teammates.remove(teammate.target)
            else:
                teammate_not_exists.append(teammate.target)
    await orm.update(
        GroupTeam,
        [GroupTeam.name == team_name, GroupTeam.group_id == group.id],
        {"teammates": '|'.join(map(str, teammates))}
    )
    op = "添加" if op in ("添加成员", "add") else "移除"
    await app.sendGroupMessage(
        group,
        MessageChain(
            f"已成功为小组  <{team_name}> {op}{modify_count}位成员，当前小组成员如下：\n" +
            "\n".join([(await app.getMember(group, member)).name for member in teammates])
        ),
        quote=source
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("群小组", "group_team"),
                UnionMatch("通知", "呼叫", "notice", "call"),
                RegexMatch(r"[\S]+") @ "team_name",
                WildcardMatch().flags(re.S) @ "message"
            ])
        ],
        decorators=[
            FrequencyLimit.require("group_team_notice", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            Permission.require(Permission.GROUP_ADMIN),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def group_team_notice(
    app: Ariadne, group: Group, source: Source, team_name: RegexResult, message: RegexResult
):
    team_name = team_name.result.asDisplay().strip()
    message = message.result
    if not await team_exists(group, team_name):
        return await app.sendGroupMessage(
            group,
            MessageChain(f"小组 {team_name} 不存在！请更换名称或使用 `群小组 创建分组 {team_name} <@要加入的成员>` 命令新建小组！"),
            quote=source
        )
    teammates = await get_teammates(group, team_name)
    await app.sendGroupMessage(
        group,
        MessageChain(' ').join([MessageChain([At(teammate)]) for teammate in teammates]) +
        ' ' + message if message else ""
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("群小组", "group_team"),
                UnionMatch("列出", "显示", "列表", "show", "list"),
                RegexMatch(r"[\S]+", optional=True) @ "team_name"
            ])
        ],
        decorators=[
            FrequencyLimit.require("group_team_show", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            Permission.require(Permission.GROUP_ADMIN),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def group_team_show(app: Ariadne, group: Group, source: Source, team_name: RegexResult):
    if team_name.matched:
        team_name = team_name.result.asDisplay().strip()
        if not await team_exists(group, team_name):
            await app.sendGroupMessage(
                group,
                MessageChain(f"小组 {team_name} 不存在！请检查名称！"),
                quote=source
            )
        else:
            teammates = await get_teammates(group, team_name)
            await app.sendGroupMessage(
                group, MessageChain(f"小组 <{team_name}> 有如下{len(teammates)}名成员：\n") +
                "\n".join([(await app.getMember(group, member)).name for member in teammates])
            )
    else:
        teams = await orm.fetchall(
            select(
                GroupTeam.name, GroupTeam.teammates, GroupTeam.creator
            ).where(
                GroupTeam.group_id == group.id
            )
        )
        await app.sendGroupMessage(
            group, MessageChain(
                f"群组 <{group.name}> 有如下{len(teams)}个小组：\n" +
                '\n'.join([
                    f"<{team[0]}>  人数：{len(team[1].split('|'))}  创建者：{(await app.getMember(group, team[2])).name}"
                    for team in teams
                ])
            ),
            quote=source
        )


async def team_exists(group: Union[Group, int], name: str) -> bool:
    group = group.id if isinstance(group, Group) else group
    return bool(await orm.fetchone(select(GroupTeam).where(GroupTeam.name == name, GroupTeam.group_id == group)))


async def get_team(group: Union[Group, int], name: str):
    group = group.id if isinstance(group, Group) else group
    return await orm.fetchone(
        select(
            GroupTeam.name, GroupTeam.group_id, GroupTeam.creator, GroupTeam.teammates
        ).where(
            GroupTeam.name == name, GroupTeam.group_id == group
        )
    )


async def get_teammates(group: Union[Group, int], name: str) -> List[int]:
    team = await get_team(group, name)
    return list(map(int, team[3].split('|'))) if team else []
