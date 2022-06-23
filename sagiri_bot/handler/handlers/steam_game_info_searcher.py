import re

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight, SpacePolicy
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, WildcardMatch, RegexResult

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("SteamGameInfoSearch")
channel.author("SAGIRI-kawaii")
channel.description("一个可以搜索steam游戏信息的插件，在群中发送 `steam {游戏名}` 即可")

core = AppCore.get_core_instance()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ""


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("steam").space(SpacePolicy.FORCE),
                WildcardMatch().flags(re.DOTALL) @ "keyword",
            ])
        ],
        decorators=[
            FrequencyLimit.require("steam_game_info_searcher", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def steam_game_info_searcher(
    app: Ariadne, message: MessageChain, group: Group, keyword: RegexResult
):
    keyword = keyword.result.asDisplay()
    await app.sendGroupMessage(
        group, await get_steam_game_search(keyword), quote=message.getFirst(Source)
    )


async def get_steam_game_description(game_id: int) -> str:
    """
    Return game description on steam

    Args:
        game_id: Steam shop id of target game

    Examples:
        get_steam_game_description(502010)

    Return:
        str
    """
    url = f"https://store.steampowered.com/app/{game_id}/"
    async with get_running(Adapter).session.get(url=url, proxy=proxy) as resp:
        html = await resp.text()
    description = re.findall(
        r'<div class="game_description_snippet">(.*?)</div>', html, re.S
    )
    if len(description) == 0:
        return "none"
    return description[0].strip()


async def get_steam_game_search(keyword: str) -> MessageChain:
    url = f"https://steamstats.cn/api/steam/search?q={keyword}&page=1&format=json&lang=zh-hans"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6",
        "pragma": "no-cache",
        "referer": "https://steamstats.cn/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/85.0.4183.121 Safari/537.36 ",
    }

    async with get_running(Adapter).session.get(url=url, headers=headers) as resp:
        result = await resp.json()

    if len(result["data"]["results"]) == 0:
        return MessageChain(f"搜索不到{keyword}呢~检查下有没有吧~偷偷告诉你，搜英文名的效果可能会更好哟~")
    else:
        result = result["data"]["results"][0]
        async with get_running(Adapter).session.get(url=result["avatar"]) as resp:
            img_content = await resp.read()
        description = await get_steam_game_description(result["app_id"])
        return MessageChain(
            [
                Plain(text="\n搜索到以下信息：\n"),
                Plain(text=f"游戏：{result['name']} ({result['name_cn']})\n"),
                Plain(text=f"游戏id：{result['app_id']}\n"),
                Image(data_bytes=img_content),
                Plain(text=f"游戏描述：{description}\n"),
                Plain(
                    text=f"\nSteamUrl:https://store.steampowered.com/app/{result['app_id']}/"
                ),
            ]
        )
