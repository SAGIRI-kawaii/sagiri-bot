import re
import json
import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free

saya = Saya.current()
channel = Channel.current()

channel.name("HotWordsExplainer")
channel.author("SAGIRI-kawaii")
channel.description("一个可以查询热门词的插件，在群中发送 `{keyword}是什么梗`")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def hot_words_explainer_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await HotWordsExplainer.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class HotWordsExplainer(AbstractHandler):
    __name__ = "HotWordsExplainer"
    __description__ = "一个可以查询热门词的插件"
    __usage__ = "在群中发送 `{keyword}是什么梗"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(r".+是什么梗", message.asDisplay()):
            if keyword := message.asDisplay()[:-4].strip():
                return await HotWordsExplainer.get_result(group, member, keyword)

    @staticmethod
    @frequency_limit_require_weight_free(1)
    async def get_result(group: Group, member: Member, keyword: str) -> MessageItem:
        url = "https://api.jikipedia.com/go/search_definitions"
        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        payload = {"phrase": keyword, "page": 1}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=json.dumps(payload)) as resp:
                result = await resp.json()
        if "category" in result.keys():
            if result["category"] == "ban_enabled":
                return MessageItem(
                    MessageChain.create([
                        Plain(text="请求过多，已达到访问上限，请稍后再试。")
                    ]),
                    QuoteSource()
                )
        result = result["data"][0]
        return MessageItem(
            MessageChain.create([
                Plain(text=f"{result['term']['title']}\n\n"),
                Plain(text=f"标签：{'、'.join(tag['name'] for tag in result['tags'])}\n\n"),
                Plain(text=f"释义：{result['content']}")
            ]),
            QuoteSource()
        )
