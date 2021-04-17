from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.static_datas import pinyin, emoji
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource


def get_pinyin(char: str):
    if char in pinyin:
        return pinyin[char]
    else:
        return "None"


class AbstractMessageTransformHandler(AbstractHandler):
    __name__ = "AbstractMessageTransformHandler"
    __description__ = "一个普通话转抽象话的Handler"
    __usage__ = "在群中发送 `/抽象 文字` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("/抽象 "):
            set_result(message, await self.transform_abstract_message(message.asDisplay()[4:]))
        else:
            return None

    @staticmethod
    async def transform_abstract_message(content: str) -> MessageItem:
        result = ""
        length = len(content)
        index = 0
        while index < length:
            if index < length - 1 and (get_pinyin(content[index]) + get_pinyin(content[index + 1])) in emoji:
                result += emoji[get_pinyin(content[index]) + get_pinyin(content[index + 1])]
                index += 1
            elif get_pinyin(content[index]) in emoji:
                result += emoji[get_pinyin(content[index])]
            else:
                result += content[index]
            index += 1
        return MessageItem(
            MessageChain.create([Plain(text=result)]),
            QuoteSource(GroupStrategy())
        )
