from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    RegexMatch,
    MatchResult,
    ElementMatch,
    ElementResult,
)

from .utils import get_review
from shared.utils.type import parse_match_type
from shared.utils.permission import user_permission_require
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("GroupWordCloud")
channel.author("SAGIRI-kawaii")
channel.description("群词云生成器，" "在群中发送 `[我的|本群][日|月|年]内总结` 即可查看个人/群 月/年词云（群词云需要权限等级2）")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("我的", "本群") @ "scope",
                UnionMatch("年内", "月内", "日内", "今日", "本月", "本年", "年度", "月度") @ "period",
                UnionMatch("总结", "词云"),
                RegexMatch(r"[0-9]+", optional=True) @ "top_k",
                RegexMatch(r"[\s]", optional=True),
                ElementMatch(Image, optional=True) @ "mask",
                RegexMatch(r"[\s]", optional=True),
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("group_wordcloud", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def group_wordcloud(
    app: Ariadne,
    group: Group,
    member: Member,
    source: Source,
    scope: MatchResult,
    period: MatchResult,
    top_k: MatchResult,
    mask: ElementResult,
):
    scope = "group" if scope.result.display == "本群" else "member"
    if scope == "group" and not await user_permission_require(group, member, 2):
        return await app.send_group_message(
            group, MessageChain([Plain(text="权限不足呢~爪巴!")]), quote=source
        )

    period = period.result.display
    top_k = min(parse_match_type(top_k, int, 1000), 100000) if top_k.matched else 1000
    if scope == "group":
        member = None
    await app.send_group_message(
        group, await get_review(group, member, period, mask.result, top_k), quote=source,
    )
