import json
import aiohttp

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, RegexResult

from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()

channel.name("HotWordsExplainer")
channel.author("SAGIRI-kawaii")
channel.description("一个可以查询热门词的插件，在群中发送 `{keyword}是什么梗`")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([RegexMatch(r"[^\s]+") @ "keyword", FullMatch("是什么梗")])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("hot_words_explainer", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def hot_words_explainer(app: Ariadne, group: Group, source: Source, keyword: RegexResult):
    await app.send_group_message(group, await get_result(keyword.result.display), quote=source)


async def get_result(keyword: str) -> MessageChain:
    url = "https://api.jikipedia.com/go/search_definitions"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Host": "api.jikipedia.com",
        "Origin": "https://jikipedia.com",
        "Referer": "https://jikipedia.com/",
        "XID": "ZMURkzbTb+tAIYIRxJaCKfLAyoZp2WaHkDB5NQD9tdwYI26H8qyRzMSwl8KLKVhVy6Xu37EwTlNmyP6CXS2aIM0iwIOAy64JSyXFDyk2EHk="
    }
    payload = {"phrase": keyword, "page": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=json.dumps(payload)) as resp:
            result = await resp.json()
    if result.get("category") == "ban_enabled":
        return MessageChain("请求过多，已达到访问上限，请稍后再试。")
    print(result)
    result = result["data"]
    get = False
    for res in result:
        if definition := res.get("definitions"):
            result = definition[0]
            get = True
            break
    if not get:
        return MessageChain(f"未找到关于{keyword}的结果！")
    return MessageChain([
        f"{result['term']['title']}\n\n",
        f"标签：{'、'.join(tag['name'] for tag in result['tags'])}\n\n",
        f"释义：{result['content']}",
    ])
