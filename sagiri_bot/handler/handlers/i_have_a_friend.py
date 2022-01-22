from io import BytesIO

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, At
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import RegexMatch, FullMatch, ElementMatch

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.utils import BuildImage, get_avatar
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("IHaveAFriend")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个生成假聊天记录插件，\n"
    "在群中发送 "
    "`我(有一?个)?朋友(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问) [-dark] [@target] 内容` "
    "即可 [@目标]"
)

core = AppCore.get_core_instance()
config = core.get_config()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [
                        FullMatch("我"),
                        RegexMatch(r"有一?个", optional=True),
                        FullMatch("朋友"),
                        RegexMatch(r"(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问)"),
                        FullMatch(" ", optional=True)
                    ],
                    {
                        "dark": FullMatch("-dark", optional=True),
                        "target": ElementMatch(At, optional=True),
                        "content": RegexMatch(".+", optional=True)
                    }
                )
            )
        ]
    )
)
async def i_have_a_friend(
        app: Ariadne,
        message: MessageChain,
        group: Group,
        member: Member,
        content: RegexMatch,
        target: ElementMatch,
        dark: FullMatch
):
    if result := await IHaveAFriend.handle(app, message, group, member, content, target, dark):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class IHaveAFriend(AbstractHandler):
    __name__ = "IHaveAFriend"
    __description__ = "一个生成假聊天记录插件"
    __usage__ = "在群中发送 `我(有一?个)?朋友(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问) 内容 [@目标]` 即可"
    __origin__ = "https://github.com/HibiKier/zhenxun_bot"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(
            app: Ariadne,
            message: MessageChain,
            group: Group,
            member: Member,
            content: RegexMatch,
            target: ElementMatch,
            dark: FullMatch
    ):
        if content.matched and content.result.asDisplay().strip():
            content = content.result.asDisplay()
            if target.matched:
                target = target.result.target
                member = await app.getMember(group, target)
                if not member:
                    return MessageItem(MessageChain.create([Plain(text="获取成员信息失败！")]), QuoteSource())
            else:
                target = member
            if avatar := await get_avatar(target, 160):
                avatar = BuildImage(200, 100, background=BytesIO(avatar))
            else:
                avatar = BuildImage(200, 100, color=(0, 0, 0))
            avatar.circle_new()
            text = BuildImage(300, 30, font_size=30, color="white" if not dark.matched else "black")
            text.text((0, 0), member.name, (0, 0, 0) if not dark.matched else (141, 141, 146))
            A = BuildImage(700, 150, font_size=25, color="white" if not dark.matched else "black")
            A.paste(avatar, (30, 25), True)
            A.paste(text, (150, 38))
            A.text((150, 85), content.strip(), (125, 125, 125) if not dark.matched else (255, 255, 255))
            return MessageItem(MessageChain.create([Image(data_bytes=A.pic2bytes())]), QuoteSource())
        else:
            return MessageItem(MessageChain.create([Plain(text="都不知道问什么")]), QuoteSource())
