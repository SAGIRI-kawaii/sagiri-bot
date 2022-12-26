import re
from datetime import datetime

import aiohttp
from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Source, ForwardNode, Forward
from graia.ariadne.message.parser.twilight import Twilight, SpacePolicy, ArgumentMatch, ArgResult
from graia.ariadne.message.parser.twilight import WildcardMatch, RegexResult
from graia.ariadne.model import Member
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from shared.models.config import GlobalConfig
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)
from shared.utils.module_related import get_command
from shared.utils.text2img import html2img
from shared.utils.type import parse_match_type

channel = Channel.current()
channel.name("SteamGameInfoSearch")
channel.author("SAGIRI-kawaii")
channel.description("一个可以搜索steam游戏信息的插件，在群中发送 `steam {游戏名}` 即可")

config = create(GlobalConfig)
proxy = config.proxy if config.proxy != "proxy" else ""


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module).space(SpacePolicy.FORCE),
                ArgumentMatch("-n", optional=True) @ "max_num",
                WildcardMatch().flags(re.DOTALL) @ "keyword",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("steam_game_info_searcher", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def steam_game_info_searcher(
        app: Ariadne, group: Group, keyword: RegexResult, source: Source, sender: Member,
        max_num: ArgResult,
):
    max_num = parse_match_type(max_num, int, 1)
    keyword = keyword.result.display
    await app.send_message(group, MessageChain(
        f"搜索ing"
    ), quote=source)
    message = await get_steam_game_search(keyword, max_num)
    if len(message) > 1:
        fwd_nodeList = [
            ForwardNode(
                target=sender,
                time=datetime.now(),
                message=MessageChain(temp),
            ) for temp in message
        ]
        message_send = MessageChain(Forward(nodeList=fwd_nodeList))
    else:
        message_send = message[0]
    try:
        bot_msg = await app.send_message(group, MessageChain(
            message_send
        ), quote=source)
        if bot_msg.id == -1:
            raise Exception("消息风控")
        if len(message) > 1:
            return await app.send_message(group, MessageChain(
                f"请点击转发消息查看!"
            ), quote=source)
    except:
        return await app.send_message(group, MessageChain(
            f"ERROR:消息风控~"
        ), quote=source)


async def get_steam_game_info(game_id: int) -> tuple:
    url = f"https://steamdb.info/app/{game_id}/"
    headers = {
        'Host': 'steamdb.info',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
        'Accept': ' text/html:application/xhtml+xml',
        'Accept-Language': ' zh-CN:zh;q=0.8',
        'Alt-Used': ' steamdb.info',
        'Connection': ' keep-alive',
        'Cookie': ' cf_clearance=80PGTWGLdKtpjgXnXwe1Sr6nY16YP_f_DaacZSoDIfk-1672033992-0-160; '
                  '__Host-cc=cn; '
                  '__cf_bm=.VYaxYTDzLQiMC0WjjmbOqaHgSUvjUsLVaxAjLiZlIM-1672033979-0-AUkbvtmhv/Yr2jDmiV0FeXU+/3ENlCJBHsOAs7WX5Yk1anaRDu51g0qnQ3ljHIv3kyp79/S5Q9FtftZM2qblYd4=; '
                  'cf_chl_2=ddb9b7327aa006c; '
                  'cf_chl_rc_m=1',
        'Upgrade-Insecure-Requests': ' 1',
        'Sec-Fetch-Dest': ' document',
        'Sec-Fetch-Mode': ' navigate',
        'Sec-Fetch-Site': ' none',
        'Sec-Fetch-User': ' ?1'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, proxy=proxy, headers=headers) as resp:
            html = await resp.text()
    des = re.findall(
        r'<p class="header-description" itemprop="description">(.*?)</p>', html, re.S
    )
    des = des[0].strip() if len(des) != 0 else None
    info = re.findall(
        r'<table class="table table-bordered table-hover table-responsive-flex">(.*?)</table>', html, re.S
    )
    info = f'<table class="table table-bordered table-hover table-responsive-flex">{info[0].strip()}</table>' if len(
        info) != 0 else None
    in_game = re.findall(
        r'<div class="header-thing-number">(.*?)</div>', html, re.S
    )
    in_game = in_game[0].strip() if len(in_game) != 0 else None
    think_good = re.findall(
        r'<div class="header-thing-number header-thing-good">(.*?)</div>', html, re.S
    )
    think_good = think_good[0].strip() if len(think_good) != 0 else None
    price = re.findall(
        r'<div class="table-responsive">(.*?)</div>', html, re.S
    )
    price = price[0].strip() if len(price) != 0 else None
    return des, info, in_game, think_good, price


async def get_steam_game_description(game_id: int) -> str:
    url = f"https://store.steampowered.com/app/{game_id}/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, proxy=proxy) as resp:
            html = await resp.text()
    description = re.findall(r'<div class="game_description_snippet">(.*?)</div>', html, re.S)
    if len(description) == 0:
        return "none"
    return description[0].strip()


async def get_steam_game_search(keyword: str, max_num: int) -> list[MessageChain]:
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
    url = f"https://steamstats.cn/api/steam/search?q={keyword}&page=1&format=json&lang=zh-hans"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as resp:
            result = await resp.json()

    if len(result["data"]["results"]) == 0:
        return MessageChain(f"搜索不到{keyword}呢~检查下有没有吧~偷偷告诉你，搜英文名的效果可能会更好哟~")
    message = []
    for item in result["data"]["results"][:max_num]:
        async with aiohttp.ClientSession() as session:
            if item["avatar"] != "":
                async with session.get(url=item["avatar"]) as resp:
                    img_content = await resp.read()
            else:
                img_content = None
        des, info, in_game, think_good, price = await get_steam_game_info(item["app_id"])
        message.append(
            MessageChain(
                [
                    Plain(text=f"游戏：{item['name']} ({item['name_cn']})\n"),
                    Plain(text=f"游戏id：{item['app_id']}\n"),
                    Image(data_bytes=img_content) if img_content else '',
                    Plain(text=f"\n"),
                    Plain(text=f"游戏描述：{des}\n"),
                    Plain(text=f"基本信息：\n"),
                    Image(data_bytes=await html2img(info)) if info else "没获取到信息，别白费力气了捏~",
                    Plain(text=f"\n"),
                    Plain(text=f"好评率：{think_good}  "),
                    Plain(text=f"当前在线：{in_game}\n"),
                    Plain(text=f"价格：\n"),
                    Image(data_bytes=await html2img(price)) if info else "None",
                    Plain(text=f"\n"),
                    Plain(
                        text=f"SteamUrl:https://store.steampowered.com/app/{item['app_id']}/"
                    ),
                ]
            )
        )
    return message
