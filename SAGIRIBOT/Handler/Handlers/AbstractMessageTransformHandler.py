from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.static_datas import pinyin, emoji
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource


def get_pinyin(char: str):
    if char in pinyin:
        return pinyin[char]
    else:
        return "None"


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abstract_message_transform_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await AbstractMessageTransformHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class AbstractMessageTransformHandler(AbstractHandler):
    __name__ = "AbstractMessageTransformHandler"
    __description__ = "一个普通话转抽象话的Handler"
    __usage__ = "在群中发送 `/抽象 文字` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("/抽象 "):
            return await AbstractMessageTransformHandler.transform_abstract_message(message.asDisplay()[4:])
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
