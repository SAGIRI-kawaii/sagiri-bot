from io import BytesIO

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Image, At, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, ElementMatch, RegexResult, ElementResult

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.utils import BuildImage, get_avatar

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

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
            Twilight([
                FullMatch("我"),
                RegexMatch(r"有一?个", optional=True),
                FullMatch("朋友"),
                RegexMatch(r"(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问)"),
                FullMatch(" ", optional=True),
                FullMatch("-dark", optional=True) @ "dark",
                ElementMatch(At, optional=True) @ "target",
                RegexMatch(".+", optional=True) @ "content"
            ])
        ],
        decorators=[
            FrequencyLimit.require("i_have_a_friend", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def i_have_a_friend(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    content: RegexResult,
    target: ElementResult,
    dark: RegexResult
):
    if content.matched and content.result.asDisplay().strip():
        content = content.result.asDisplay()
        if target.matched:
            target = target.result.target
            member = await app.getMember(group, target)
            if not member:
                await app.sendGroupMessage(group, MessageChain("获取成员信息失败！"), quote=message.getFirst(Source))
                return
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
        await app.sendGroupMessage(group, MessageChain([Image(data_bytes=A.pic2bytes())]), quote=message.getFirst(Source))
    else:
        await app.sendGroupMessage(group, MessageChain("都不知道问什么"), quote=message.getFirst(Source))
