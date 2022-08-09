import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import WildcardMatch, RegexResult

from sagiri_bot.internal_utils import get_command
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("ApexStat")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个Apex数据查询插件，\n"
    "在群中发送 `/apex origin用户名` 即可"
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    get_command(__file__, channel.module),
                    WildcardMatch() @ "player",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("apex_stat", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def apex_stat(
    app: Ariadne,
    group: Group,
    source: Source,
    player: RegexResult
):
    url = f"https://www.jumpmaster.xyz/user/Stats?platform=PC&player={player.result.display.strip()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    user = data["user"]
    user_name = user.get("username", "null")
    status = user.get("status", {})
    online = bool(status.get("online"))
    in_game = bool(status.get("ingame"))
    party_in_match = bool(status.get("partyInMatch"))
    if in_game:
        match_length = status.get("matchLength")
        if match_length:
            match_length = f"{match_length // 60}分钟{match_length % 60}秒"
        current_status = f"正在游戏，游戏时长{match_length}"
    elif party_in_match:
        current_status = "正在匹配"
    elif online:
        current_status = "在线"
    else:
        current_status = "离线"
    bans = user.get("bans", {})
    bans_active = bool(bans.get("active"))
    bans_length = bans.get("length")
    bans_reason = bans.get("reason")
    if bans_active:
        if bans_length:
            bans_length = f"{bans_length // 60}分钟{bans_length % 60}秒"
        bans_status = f"封禁中\n封禁时长：{bans_length}\n封禁原因：{bans_reason}"
    else:
        bans_status = "未封禁"
    account = data["account"]
    level = account.get("level")
    ranked = data["ranked"]
    br = ranked.get("BR", {})
    br_score = br.get("score")
    br_name = br.get("name").strip()
    br_division = br.get("division")
    arenas = ranked.get("Arenas", {})
    arenas_score = arenas.get("score")
    arenas_name = arenas.get("name").strip()
    arenas_division = arenas.get("division")
    result = f"用户名：{user_name}\n"
    result += f"用户等级：{level}\n"
    result += f"当前状态：{current_status}\n"
    result += f"封禁状态：{bans_status}\n"
    result += f"大逃杀分数：{br_score}\n"
    result += f"大逃杀段位: {br_name} {br_division}\n"
    result += f"竞技场分数：{arenas_score}\n"
    result += f"竞技场段位: {arenas_name} {arenas_division}"
    await app.send_group_message(group, MessageChain(result), quote=source)
