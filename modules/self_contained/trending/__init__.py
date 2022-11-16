

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import UnionMatch, RegexResult

from .utils import get_github_trending, get_weibo_trending, get_zhihu_trending
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()

channel.name("Trending")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个获取热搜的插件\n"
    "在群中发送 `微博热搜` 即可查看微博热搜\n"
    "在群中发送 `知乎热搜` 即可查看知乎热搜\n"
    "在群中发送 `github热搜` 即可查看github热搜"
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([UnionMatch("微博热搜", "知乎热搜", "github热搜") @ "trending_type"])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("trending", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def trending(app: Ariadne, group: Group, trending_type: RegexResult):
    trending_type = trending_type.result.display
    if trending_type == "微博热搜":
        await app.send_group_message(group, await get_weibo_trending())
    elif trending_type == "知乎热搜":
        await app.send_group_message(group, await get_zhihu_trending())
    elif trending_type == "github热搜":
        await app.send_group_message(group, await get_github_trending())
