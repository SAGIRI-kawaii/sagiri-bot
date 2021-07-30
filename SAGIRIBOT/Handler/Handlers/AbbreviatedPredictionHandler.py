import re
import aiohttp

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.Strategy import QuoteSource
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount
from SAGIRIBOT.decorators import frequency_limit_require_weight_free, switch, blacklist

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await AbbreviatedPredictionHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class AbbreviatedPredictionHandler(AbstractHandler):
    __name__ = "AbbreviatedPredictionHandler"
    __description__ = "一个获取英文缩写意思的Handler"
    __usage__ = "在群中发送 `缩 内容` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if re.match(r'缩\s?[A-Za-z0-9]+', message_text):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            abbreviation = message_text[1:].strip()
            return await AbbreviatedPredictionHandler.get_abbreviation_explain(group, member, abbreviation)
        else:
            return None

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
            MessageChain.create([Plain(text=result if has_result else "没有找到结果哦~")]),
            QuoteSource(GroupStrategy())
        )
