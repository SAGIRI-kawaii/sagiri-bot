import aiohttp
from io import BytesIO

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import RegexMatch, FullMatch, ElementMatch

from sagiri_bot.utils import BuildImage
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender


saya = Saya.current()
channel = Channel.current()

channel.name("BWGrass")
channel.author("SAGIRI-kawaii")
channel.description("一个生成黑白草的插件，在群中发送 `黑白[草]图 内容 图片` 即可")

core = AppCore.get_core_instance()
config = core.get_config()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [FullMatch("黑白"), FullMatch("草", optional=True), FullMatch("图")],
                    {"content": RegexMatch(r".+"), "image": ElementMatch(Image)}
                )
            )
        ]
    )
)
async def black_white_grass(
        app: Ariadne,
        message: MessageChain,
        group: Group,
        member: Member,
        content: RegexMatch,
        image: ElementMatch
):
    if result := await BWGrass.handle(app, message, group, member, content, image):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class BWGrass(AbstractHandler):
    __name__ = "BWGrass"
    __description__ = "一个生成黑白草的插件"
    __usage__ = "在群中发送 `黑白[草]图 内容 图片` 即可"
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
            image: ElementMatch
    ):
        msg = content.result.asDisplay()
        img = await image.result.get_bytes()
        msg = await get_translate(msg)
        w2b = BuildImage(0, 0, background=BytesIO(img))
        w2b.convert("L")
        msg_sp = msg.split("<|>")
        w, h = w2b.size
        add_h, font_size = init_h_font_size(h)
        bg = BuildImage(w, h + add_h, color="black", font_size=font_size)
        bg.paste(w2b)
        chinese_msg = formalization_msg(msg)
        if not bg.check_font_size(chinese_msg):
            if len(msg_sp) == 1:
                centered_text(bg, chinese_msg, add_h)
            else:
                centered_text(bg, chinese_msg + "<|>" + msg_sp[1], add_h)
        elif not bg.check_font_size(msg_sp[0]):
            centered_text(bg, msg, add_h)
        else:
            ratio = (bg.getsize(msg_sp[0])[0] + 20) / bg.w
            add_h = add_h * ratio
            bg.resize(ratio)
            centered_text(bg, msg, add_h)
        return MessageItem(MessageChain.create([Image(data_bytes=bg.pic2bytes())]), QuoteSource())


def centered_text(img: BuildImage, text: str, add_h: int):
    top_h = img.h - add_h + (img.h / 100)
    bottom_h = img.h - (img.h / 100)
    text_sp = text.split("<|>")
    w, h = img.getsize(text_sp[0])
    if len(text_sp) == 1:
        w = int((img.w - w) / 2)
        h = int(top_h + (bottom_h - top_h - h) / 2)
        img.text((w, h), text_sp[0], (255, 255, 255))
    else:
        br_h = int(top_h + (bottom_h - top_h) / 2)
        w = int((img.w - w) / 2)
        h = int(top_h + (br_h - top_h - h) / 2)
        img.text((w, h), text_sp[0], (255, 255, 255))
        w, h = img.getsize(text_sp[1])
        w = int((img.w - w) / 2)
        h = int(br_h + (bottom_h - br_h - h) / 2)
        img.text((w, h), text_sp[1], (255, 255, 255))


async def get_translate(msg: str) -> str:
    url = f"http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule&smartresult=ugc&sessionFrom=null"
    data = {
        "type": "ZH_CN2JA",
        "i": msg,
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "ue": "UTF-8",
        "action": "FY_BY_CLICKBUTTON",
        "typoResult": "true",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            data = await resp.json()
    if data["errorCode"] == 0:
        translate = data["translateResult"][0][0]["tgt"]
        msg += "<|>" + translate
    return msg


def formalization_msg(msg: str) -> str:
    rst = ""
    for i in range(len(msg)):
        if is_chinese(msg[i]):
            rst += msg[i] + " "
        else:
            rst += msg[i]
        if i + 1 < len(msg) and is_chinese(msg[i + 1]) and msg[i].isalpha():
            rst += " "
    return rst


def init_h_font_size(h):
    #       高度      字体
    if h < 400:
        return init_h_font_size(400)
    elif 400 < h < 800:
        return init_h_font_size(800)
    return h * 0.2, h * 0.05


def is_chinese(word: str) -> bool:
    """
    说明：
        判断字符串是否为纯中文
    参数：
        :param word: 文本
    """
    for ch in word:
        if not "\u4e00" <= ch <= "\u9fff":
            return False
    return True
