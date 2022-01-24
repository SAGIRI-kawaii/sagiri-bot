import re
import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount

saya = Saya.current()
channel = Channel.current()

channel.name("SteamGameInfoSearch")
channel.author("SAGIRI-kawaii")
channel.description("一个可以搜索steam游戏信息的插件，在群中发送 `steam {游戏名}` 即可")

core = AppCore.get_core_instance()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ''


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def steam_game_info_searcher(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await SteamGameInfoSearch.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class SteamGameInfoSearch(AbstractHandler):
    __name__ = "SteamGameInfoSearch"
    __description__ = "一个可以搜索steam游戏信息的插件"
    __usage__ = "在群中发送 `steam {游戏名}` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("steam "):
            await update_user_call_count_plus(group, member, UserCalledCount.search, "search")
            return await SteamGameInfoSearch.get_steam_game_search(group, member, message.asDisplay()[6:])
        else:
            return None

    @staticmethod
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
        url = "https://store.steampowered.com/app/%s/" % game_id
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, proxy=proxy) as resp:
                html = await resp.text()
        description = re.findall(r'<div class="game_description_snippet">(.*?)</div>', html, re.S)
        if len(description) == 0:
            return "none"
        return description[0].lstrip().rstrip()

    @staticmethod
    @frequency_limit_require_weight_free(3)
    async def get_steam_game_search(group: Group, member: Member, keyword: str) -> MessageItem:
        url = "https://steamstats.cn/api/steam/search?q=%s&page=1&format=json&lang=zh-hans" % keyword
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
                          "Chrome/85.0.4183.121 Safari/537.36 "
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as resp:
                result = await resp.json()

        if len(result["data"]["results"]) == 0:
            return MessageItem(
                MessageChain.create([Plain(text=f"搜索不到{keyword}呢~检查下有没有吧~偷偷告诉你，搜英文名的效果可能会更好哟~")]),
                QuoteSource()
            )
        else:
            result = result["data"]["results"][0]
            async with aiohttp.ClientSession() as session:
                async with session.get(url=result["avatar"]) as resp:
                    img_content = await resp.read()
            description = await SteamGameInfoSearch.get_steam_game_description(result["app_id"])
            return MessageItem(
                MessageChain.create([
                    Plain(text="\n搜索到以下信息：\n"),
                    Plain(text="游戏：%s (%s)\n" % (result["name"], result["name_cn"])),
                    Plain(text="游戏id：%s\n" % result["app_id"]),
                    Image(data_bytes=img_content),
                    Plain(text="游戏描述：%s\n" % description),
                    Plain(text="\nSteamUrl:https://store.steampowered.com/app/%s/" % result["app_id"])
                ]),
                QuoteSource()
            )
