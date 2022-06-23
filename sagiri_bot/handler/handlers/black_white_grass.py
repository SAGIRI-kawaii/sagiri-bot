import aiohttp
from io import BytesIO

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, ElementMatch, RegexResult, ElementResult

from sagiri_bot.utils import BuildImage
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()

channel.name("BWGrass")
channel.author("SAGIRI-kawaii")
channel.description("一个生成黑白草图的插件，在群中发送 `黑白[草]图 内容 图片` 即可")
channel.meta["origin"] = "https://github.com/HibiKier/zhenxun_bot"

core = AppCore.get_core_instance()
config = core.get_config()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("黑白"), FullMatch("草", optional=True), FullMatch("图"),
                RegexMatch(r".+") @ "content", ElementMatch(Image) @ "image"
            ])
        ],
        decorators=[
            FrequencyLimit.require("black_white_grass", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def black_white_grass(app: Ariadne, group: Group, content: RegexResult, image: ElementResult):
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
    await app.sendGroupMessage(group, MessageChain([Image(data_bytes=bg.pic2bytes())]))


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
        rst += msg[i] + " " if is_chinese(msg[i]) else msg[i]
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
    return all("\u4e00" <= ch <= "\u9fff" for ch in word)
