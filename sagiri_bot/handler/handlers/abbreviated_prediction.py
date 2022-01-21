import re
import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import RegexMatch, FullMatch

from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount
from sagiri_bot.decorators import frequency_limit_require_weight_free, switch, blacklist

saya = Saya.current()
channel = Channel.current()

channel.name("AbbreviatedPrediction")
channel.author("SAGIRI-kawaii")
channel.description("一个获取英文缩写意思的插件，在群中发送 `缩 内容` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [FullMatch("缩"), FullMatch(" ", optional=True)],
                    {"content": RegexMatch(r"[A-Za-z0-9]+")}
                )
            )
        ]
    )
)
async def abbreviated_prediction(app: Ariadne, message: MessageChain, group: Group, member: Member, content: RegexMatch):
    if result := await AbbreviatedPrediction.handle(app, message, group, member, content):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class AbbreviatedPrediction(AbstractHandler):
    __name__ = "AbbreviatedPrediction"
    __description__ = "一个获取英文缩写意思的插件"
    __usage__ = "在群中发送 `缩 内容` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member, content: RegexMatch):
        await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
        return await AbbreviatedPrediction.get_abbreviation_explain(group, member, content.result.asDisplay())

    @staticmethod
    @frequency_limit_require_weight_free(1)
    async def get_abbreviation_explain(group: Group, member: Member, abbreviation: str) -> MessageItem:
        url = "https://lab.magiconch.com/api/nbnhhsh/guess"
        headers = {
            "referer": "https://lab.magiconch.com/nbnhhsh/"
        }
        data = {
            "text": abbreviation
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=data) as resp:
                res = await resp.json()

        result = "可能的结果:\n\n"
        has_result = False
        for i in res:
            if "trans" in i:
                if i["trans"]:
                    has_result = True
                    result += f"{i['name']} => {'，'.join(i['trans'])}\n\n"
                else:
                    result += f"{i['name']} => 没找到结果！\n\n"
            else:
                if i["inputting"]:
                    has_result = True
                    result += f"{i['name']} => {'，'.join(i['inputting'])}\n\n"
                else:
                    result += f"{i['name']} => 没找到结果！\n\n"

        return MessageItem(
            message=MessageChain.create([Plain(text=result if has_result else "没有找到结果哦~")]),
            strategy=QuoteSource()
        )
