import re
import json
import aiohttp

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def hot_words_explainer_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await HotWordsExplainerHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class HotWordsExplainerHandler(AbstractHandler):
    __name__ = "HotWordsExplainerHandler"
    __description__ = "一个可以查询热门词的Handler"
    __usage__ = "xxx是什么梗"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r".+是什么梗", message.asDisplay()):
            if keyword := message.asDisplay()[:-4].strip():
                return await HotWordsExplainerHandler.get_result(group, member, keyword)

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
        result = result["data"][0]
        return MessageItem(
            MessageChain.create([
                Plain(text=f"{result['term']['title']}\n\n"),
                Plain(text=f"标签：{'、'.join(tag['name'] for tag in result['tags'])}\n\n"),
                Plain(text=f"释义：{result['content']}")
            ]),
            QuoteSource(GroupStrategy())
        )
