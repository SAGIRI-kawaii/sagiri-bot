import re
import random
import hashlib
from loguru import logger
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import Group, GroupMessage, Member
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, WildcardMatch, RegexResult

from utils.message_chain import *
from sagiri_bot.orm.async_orm import orm
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.orm.async_orm import KeywordReply
from sagiri_bot.utils import user_permission_require

saya = Saya.current()
channel = Channel.current()

channel.name("KeywordRespondent")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个关键字回复插件，在群中发送已添加关键词可自动回复\n"
    "在群中发送 `添加回复关键词#{keyword}#{reply}` 可添加关键词\n"
    "在群中发送 `删除回复关键词#{keyword}` 可删除关键词"
)

inc = InterruptControl(AppCore.get_core_instance().get_bcc())
regex_list = []


class NumberWaiter(Waiter.create([GroupMessage])):

    """ 超时Waiter """

    def __init__(self, group: Union[int, Group], member: Union[int, Member], max_length: int):
        self.group = group if isinstance(group, int) else group.id
        self.member = (member if isinstance(member, int) else member.id) if member else None
        self.max_length = max_length

    async def detected_event(self, app: Ariadne, group: Group, member: Member, message: MessageChain):
        if group.id == self.group and member.id == self.member:
            return int(message.asDisplay()) if message.asDisplay().isnumeric() and 0 < int(message.asDisplay()) <= self.max_length else -1


class ConfirmWaiter(Waiter.create([GroupMessage])):

    """ 超时Waiter """

    def __init__(self, group: Union[int, Group], member: Union[int, Member]):
        self.group = group if isinstance(group, int) else group.id
        self.member = (member if isinstance(member, int) else member.id) if member else None

    async def detected_event(self, app: Ariadne, group: Group, member: Member, message: MessageChain):
        if group.id == self.group and member.id == self.member:
            return True if re.match(r"[是否]", message.asDisplay()) else False


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch(r"添加"), FullMatch("群组", optional=True) @ "group_only",
                RegexMatch(r"(模糊|正则)", optional=True)  @ "op_type",
                FullMatch("回复关键词#"), RegexMatch(r"[^\s]+") @ "keyword", FullMatch("#"),
                WildcardMatch().flags(re.DOTALL) @ "response"
            ])
        ]
    )
)
async def add_keyword(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    group_only: RegexResult,
    op_type: RegexResult,
    keyword: RegexResult,
    response: RegexResult
):
    if not await user_permission_require(group, member, 2):
        await app.sendGroupMessage(group, MessageChain("权限不足，爬！"), quote=message.getFirst(Source))
        return
    op_type = ("regex" if op_type.result.asDisplay() == "正则" else "fuzzy") if op_type.matched else "fullmatch"
    response = await message_chain_to_json(response.result)
    keyword = keyword.result.asDisplay()
    reply_md5 = get_md5(response)
    if await orm.fetchone(
        select(
            KeywordReply
        ).where(
            KeywordReply.keyword == keyword.strip(),
            KeywordReply.reply_type == op_type,
            KeywordReply.reply_md5 == reply_md5,
            KeywordReply.group == (group.id if group_only.matched else -1)
        )
    ):
        await app.sendGroupMessage(group, MessageChain("重复添加关键词！进程退出"), quote=message.getFirst(Source))
        return
    await orm.add(
        KeywordReply,
        {
            "keyword": keyword,
            "group": group.id if group_only.matched else -1,
            "reply_type": op_type,
            "reply": response,
            "reply_md5": reply_md5
        }
    )
    if op_type != "fullmatch":
        regex_list.append(
            (keyword if op_type == "regex" else f"(.*){keyword}(.*)", reply_md5, group.id if group_only else -1)
        )
    await app.sendGroupMessage(group, MessageChain("关键词添加成功！"), quote=message.getFirst(Source))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch(r"删除"), FullMatch("群组", optional=True) @ "group_only",
                RegexMatch(r"(模糊|正则)", optional=True)  @ "op_type",
                FullMatch("回复关键词#"), RegexMatch(r"[^\s]+") @ "keyword"
            ])
        ]
    )
)
async def delete_keyword(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    group_only: RegexResult,
    op_type: RegexResult,
    keyword: RegexResult
):
    if not await user_permission_require(group, member, 2):
        await app.sendGroupMessage(group, MessageChain("权限不足，爬！"), quote=message.getFirst(Source))
        return
    op_type = ("regex" if op_type.result.asDisplay() == "正则" else "fuzzy") if op_type.matched else "fullmatch"
    keyword = keyword.result.asDisplay()
    if results := await orm.fetchall(
        select(
            KeywordReply.reply_type, KeywordReply.reply, KeywordReply.reply_md5
        ).where(
            KeywordReply.keyword == keyword,
            KeywordReply.reply_type == op_type
        )
    ):
        replies = list()
        for result in results:
            content_type = result[0]
            content = result[1]
            content_md5 = result[2]
            replies.append([content_type, content, content_md5])

        msg = [Plain(text=f"关键词{keyword}目前有以下数据：\n")]
        for i in range(len(replies)):
            msg.append(Plain(f"{i + 1}. "))
            msg.append(("正则" if replies[i][0] == "regex" else "模糊") if replies[i][0] != "fullmatch" else "全匹配")
            msg.append("匹配\n")
            msg.extend(json_to_message_chain(replies[i][1]).__root__)
            msg.append(Plain("\n"))
        msg.append(Plain(text="请发送你要删除的回复编号"))
        await app.sendGroupMessage(group, MessageChain.create(msg))

        number = await inc.wait(NumberWaiter(group, member, len(replies)), timeout=30)
        if number == -1:
            await app.sendGroupMessage(group, MessageChain("非预期回复，进程退出"), quote=message.getFirst(Source))
            return
        await app.sendGroupMessage(
            group,
            MessageChain([
                Plain(text="你确定要删除下列回复吗(是/否)：\n"),
                Plain(keyword),
                Plain(text="\n->\n")
            ]).extend(json_to_message_chain(replies[number - 1][1]))
        )
        if await inc.wait(ConfirmWaiter(group, member), timeout=30):
            await orm.delete(
                KeywordReply,
                [
                    KeywordReply.keyword == keyword,
                    KeywordReply.reply_md5 == replies[number - 1][2],
                    KeywordReply.reply_type == replies[number - 1][0],
                    KeywordReply.group == (group.id if group_only.matched else -1)
                ]
            )
            await app.sendGroupMessage(group, MessageChain("删除成功"), quote=message.getFirst(Source))
        else:
            await app.sendGroupMessage(group, MessageChain("非预期回复，进程退出"), quote=message.getFirst(Source))
    else:
        await app.sendGroupMessage(group, MessageChain("未检测到此关键词数据"), quote=message.getFirst(Source))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def keyword_detect(app: Ariadne, message: MessageChain, group: Group):
    if result := list(await orm.fetchall(
        select(
            KeywordReply.reply
        ).where(
            KeywordReply.keyword == message.asDisplay(),
            KeywordReply.group.in_((-1, group.id))
        )
    )):
        reply = random.choice(result)
        await app.sendGroupMessage(group, json_to_message_chain(str(reply[0])))
    else:
        response_md5 = [i[1] for i in regex_list if re.match(i[0], message.asDisplay()) and i[2] in (-1, group.id)]
        if response_md5:
            await app.sendGroupMessage(
                group,
                json_to_message_chain(
                    (await orm.fetchone(
                        select(KeywordReply.reply).where(KeywordReply.reply_md5 == random.choice(response_md5))
                    ))[0]
                )
            )


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def regex_init():
    if result := await orm.fetchall(
        select(
            KeywordReply.keyword, KeywordReply.reply_md5, KeywordReply.reply_type, KeywordReply.group
        ).where(
            KeywordReply.reply_type.in_(("regex", "fuzzy"))
        )
    ):
        regex_list.extend(list([(i[0] if i[2] == "regex" else f"(.*){i[0]}(.*)", i[1], i[3]) for i in result]))


def get_md5(data: str) -> str:
    m = hashlib.md5()
    m.update(data.encode("utf-8"))
    reply_md5 = m.hexdigest()
    return reply_md5
