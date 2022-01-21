from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import FullMatch, RegexMatch

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from statics.abstract_message_transformer_data import pinyin, emoji


def get_pinyin(char: str):
    if char in pinyin:
        return pinyin[char]
    else:
        return "None"


saya = Saya.current()
channel = Channel.current()

channel.name("AbstractMessageTransformer")
channel.author("SAGIRI-kawaii")
channel.description("一个普通话转抽象话的插件，在群中发送 `/抽象 文字` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [FullMatch("/抽象 ")],
                    {"content": RegexMatch(r".*")}
                )
            )
        ]
    )
)
async def abstract_message_transformer(
        app: Ariadne,
        message: MessageChain,
        group: Group,
        member: Member,
        content: RegexMatch
):
    if result := await AbstractMessageTransformer.handle(app, message, group, member, content):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class AbstractMessageTransformer(AbstractHandler):
    __name__ = "AbstractMessageTransformer"
    __description__ = "一个普通话转抽象话的插件"
    __usage__ = "在群中发送 `/抽象 文字` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member, content: RegexMatch):
        if content.matched:
            return await AbstractMessageTransformer.transform_abstract_message(content.result.asDisplay())
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
            message=MessageChain.create([Plain(text=result)]),
            strategy=QuoteSource()
        )
