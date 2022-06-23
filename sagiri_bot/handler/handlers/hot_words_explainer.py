import json

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, RegexResult

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()

channel.name("HotWordsExplainer")
channel.author("SAGIRI-kawaii")
channel.description("一个可以查询热门词的插件，在群中发送 `{keyword}是什么梗`")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"[^\s]+") @ "keyword", FullMatch("是什么梗")])],
        decorators=[
            FrequencyLimit.require("hot_words_explainer", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def hot_words_explainer(app: Ariadne, message: MessageChain, group: Group, keyword: RegexResult):
    await app.sendGroupMessage(group, await get_result(keyword.result.asDisplay()), quote=message.getFirst(Source))


async def get_result(keyword: str) -> MessageChain:
    url = "https://api.jikipedia.com/go/search_definitions"
    headers = {
        "Content-Type": "application/json;charset=UTF-8"
    }
    payload = {"phrase": keyword, "page": 1}
    async with get_running(Adapter).session.post(url=url, headers=headers, data=json.dumps(payload)) as resp:
        result = await resp.json()
    if result.get("category") == "ban_enabled":
        return MessageChain("请求过多，已达到访问上限，请稍后再试。")
    result = result["data"][0]
    return MessageChain([
        f"{result['term']['title']}\n\n",
        f"标签：{'、'.join(tag['name'] for tag in result['tags'])}\n\n",
        f"释义：{result['content']}"
    ])
