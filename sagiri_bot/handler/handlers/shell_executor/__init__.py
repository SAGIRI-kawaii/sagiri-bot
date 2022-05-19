"""
Shell Executor 终端执行器

Usage:      @Bot shell> [Shell]
Example:    @Bot shell> pwd

执行历史将被保存至同文件夹下的 history.txt 中
记录结构为
%Y-%m-%d %H:%M:%S    QQ号    执行的 Shell 语句
"""


import asyncio
import os
from datetime import datetime
from pathlib import Path

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    WildcardMatch,
    MatchResult,
    RegexMatch,
)
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl, Waiter
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from sagiri_bot.control import Permission

saya = Saya.current()
channel = Channel.current()

channel.name("ShellExecutor")
channel.author("nullqwertyuiop")
channel.description(
    "终端执行器，可直接从聊天窗口执行 Shell，执行记录将被保存。\n"
    "使用方法：@Bot shell> [Shell]\n"
    "使用示例：@Bot shell> pwd\n"
    "需求权限：4 级"
)

bcc = saya.broadcast
inc = InterruptControl(bcc)

data_dir = Path(__file__).parent


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At),
                    RegexMatch(r"[\n\r]?", optional=True),
                    FullMatch("shell"),
                    FullMatch(">"),
                    WildcardMatch() @ "command",
                ]
            )
        ],
        decorators=[MentionMe(), Permission.require(Permission.SUPER_ADMIN)],
    )
)
async def get_bible(app: Ariadne, event: GroupMessage, command: MatchResult):
    command = command.result.asDisplay().strip()

    @Waiter.create_using_function(listening_events=[GroupMessage])
    async def confirmation_waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if (
            waiter_group.id == event.sender.group.id
            and waiter_member.id == event.sender.id
        ):
            if waiter_message.asDisplay() == "是":
                return True
            else:
                return False

    await app.sendGroupMessage(
        event.sender.group, MessageChain("请确认是否执行以下 Shell (是/否)\n" f"{command}")
    )
    try:
        if not await asyncio.wait_for(inc.wait(confirmation_waiter), 30):
            return await app.sendGroupMessage(
                event.sender.group, MessageChain("已取消本次执行")
            )
    except asyncio.TimeoutError:
        return await app.sendGroupMessage(
            event.sender.group, MessageChain("超时，已取消本次执行")
        )
    with (data_dir / "history.txt").open("a+", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\t"
            f"{event.sender.id}\t{command}\n"
        )
    await app.sendGroupMessage(
        event.sender.group, MessageChain(os.popen(command).read())
    )
