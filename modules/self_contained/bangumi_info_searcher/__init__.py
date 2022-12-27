import aiohttp
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne

from creart import create
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from shared.models.config import GlobalConfig
from shared.utils.text2img import messagechain2img
from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)


saya = Saya.current()
channel = Channel.current()

channel.name("BangumiInfoSearcher")
channel.author("SAGIRI-kawaii")
channel.description("一个可以搜索番剧信息的插件，在群中发送 `番剧 {番剧名}` 即可")

proxy = create(GlobalConfig).proxy


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module), RegexMatch(r".+") @ "keyword"])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("bangumi_info_searcher", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def bangumi_info_searcher(app: Ariadne, group: Group, keyword: RegexResult, source: Source):
    keyword = keyword.result.display
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/84.0.4147.135 Safari/537.36 "
    }
    url = f"https://api.bgm.tv/search/subject/{keyword}?type=2&responseGroup=Large"

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers) as resp:
            data = await resp.json()

    if "code" in data.keys() and data["code"] == 404 or not data["list"]:
        await app.send_group_message(
            group,
            MessageChain(f"番剧 {keyword} 未搜索到结果！"),
            quote=source,
        )
        return

    bangumi_id = data["list"][0]["id"]
    url = "https://api.bgm.tv/subject/%s?responseGroup=medium" % bangumi_id

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url, headers=headers, proxy=proxy if proxy != "proxy" else ""
        ) as resp:
            data = await resp.json()

    name = data["name"]
    cn_name = data["name_cn"]
    summary = data["summary"]
    img_url = data["images"]["large"]
    score = data["rating"]["score"]
    rank = data["rank"] if "rank" in data.keys() else None
    rating_total = data["rating"]["total"]

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=img_url, proxy=proxy if proxy != "proxy" else ""
        ) as resp:
            img_content = await resp.read()

    await app.send_group_message(
        group,
        MessageChain([Image(data_bytes=await messagechain2img(
            MessageChain([
                Plain(text="查询到以下信息：\n"),
                Image(data_bytes=img_content),
                Plain(text=f"名字:{name}\n\n中文名字:{cn_name}\n\n"),
                Plain(text=f"简介:{summary}\n\n"),
                Plain(
                    text=f"bangumi评分:{score}(参与评分{rating_total}人)"
                ),
                Plain(
                    text=f"\n\nbangumi排名:{rank}" if rank else ""
                ),
            ]),
            img_single_line=True
        ))]),
        quote=source,
    )
