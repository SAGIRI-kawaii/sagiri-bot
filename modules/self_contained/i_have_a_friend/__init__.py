import PIL.Image
from io import BytesIO
from pathlib import Path
from PIL import ImageDraw, ImageFont

from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Image, At, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    FullMatch,
    ElementMatch,
    RegexResult,
    ElementResult,
)

from shared.models.config import GlobalConfig
from shared.utils.image import get_user_avatar
from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()

channel.name("IHaveAFriend")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个生成假聊天记录插件，\n"
    "在群中发送 "
    "`我(有一?个)?朋友(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问) [-dark] [@target] 内容` "
    "即可 [@目标]"
)

config = create(GlobalConfig)
FONT_PATH = Path.cwd() / "resources" / "fonts" / "yz.ttf"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r"(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问)"),
                FullMatch(" ", optional=True),
                FullMatch("-dark", optional=True) @ "dark",
                ElementMatch(At, optional=True) @ "target",
                RegexMatch(".+", optional=True) @ "content",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("i_have_a_friend", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def i_have_a_friend(
    app: Ariadne,
    group: Group,
    member: Member,
    source: Source,
    content: RegexResult,
    target: ElementResult,
    dark: RegexResult,
):
    if content.matched and content.result.display.strip():
        content = content.result.display.strip()
        if target.matched:
            target = target.result.target
            member = await app.get_member(group, target)
            if not member:
                return await app.send_group_message(
                    group, MessageChain("获取成员信息失败！"), quote=source
                )

        else:
            target = member
        if avatar := await get_user_avatar(target):
            avatar = PIL.Image.open(BytesIO(avatar)).resize((100, 100), PIL.Image.ANTIALIAS)
        else:
            avatar = PIL.Image.new("RGBA", (100, 100), (0, 0, 0))
        size = avatar.size
        avatar.convert("RGBA")
        ellipse_box = [0, 0, 98, 98]
        mask = PIL.Image.new("L", (400, 400), "black")
        draw = ImageDraw.Draw(mask)
        for offset, fill in (-0.5, "black"), (0.5, "white"):
            left, top = [(value + offset) * 4 for value in ellipse_box[:2]]
            right, bottom = [(value - offset) * 4 for value in ellipse_box[2:]]
            draw.ellipse([left, top, right, bottom], fill=fill)
        mask = mask.resize(size, PIL.Image.LANCZOS)
        avatar.putalpha(mask)
        text = PIL.Image.new("RGBA", (300, 30), "white" if not dark.matched else "black")
        text.convert("RGBA")
        text_draw = ImageDraw.Draw(text)
        text_font = ImageFont.truetype(str(FONT_PATH), 30)
        text_draw.text((0, 0), member.name, fill=(0, 0, 0) if not dark.matched else (141, 141, 146), font=text_font)
        a = PIL.Image.new("RGBA", (700, 150), "white" if not dark.matched else "black")
        a.convert("RGBA")
        a_draw = ImageDraw.Draw(a)
        a_font = ImageFont.truetype(str(FONT_PATH), 30)
        a.paste(avatar, (30, 25), mask=mask)
        a_draw.text((150, 85), content, fill=(125, 125, 125) if not dark.matched else (255, 255, 255), font=a_font)
        a.paste(text, (150, 38))
        buf = BytesIO()
        a.save(buf, format="PNG")
        await app.send_group_message(group, MessageChain(Image(data_bytes=buf.getvalue())), quote=source)
    else:
        await app.send_group_message(group, MessageChain("都不知道问什么"), quote=source)
