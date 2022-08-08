import base64
import hashlib
import chardet

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Source, Quote, At
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    FullMatch,
    ElementMatch,
    WildcardMatch,
    RegexResult,
    SpacePolicy,
)

from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("EncoderDecoder")
channel.author("SAGIRI-kawaii")
channel.description("一个可以编码解码的插件")

MORSE_CODE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    ", ": "--..--",
    ".": ".-.-.-",
    "?": "..--..",
    "/": "-..-.",
    "-": "-....-",
    "(": "-.--.",
    ")": "-.--.-",
}


def morse_encrypt(message):
    return "".join(
        f"{MORSE_CODE_DICT[letter]} " if letter != " " else " "
        for letter in message
    )


def morse_decrypt(message):
    message += " "
    decipher = ""
    citext = ""
    i = 0
    for letter in message:
        if letter != " ":
            i = 0
            citext += letter
        else:
            i += 1
            if i == 2:
                decipher += " "
            else:
                decipher += list(MORSE_CODE_DICT.keys())[
                    list(MORSE_CODE_DICT.values()).index(citext)
                ]
                citext = ""
    return decipher


SPECIAL_TYPE = {
    "md5": {"encode": lambda x: hashlib.md5(x.encode()).hexdigest().upper()},
    "base64": {
        "encode": lambda x: base64.b64encode(x.encode()).decode("utf-8"),
        "decode": lambda x: base64.b64decode(x.encode()).decode("utf-8"),
    },
    "morse": {
        "encode": lambda x: morse_encrypt(x.upper())
        if all(i.upper() in MORSE_CODE_DICT for i in x)
        else f"只支持以下字符：{'、'.join(MORSE_CODE_DICT.keys())}",
        "decode": lambda x: morse_decrypt(x),
    },
}
SUPPORT_TYPE = {"gbk", "gb2132", "utf-8", "utf-16", "unicode_escape"}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    FullMatch("encode").space(SpacePolicy.FORCE),
                    RegexMatch(r"[\S]+").help("要转换的编码") @ "code",
                    WildcardMatch(optional=True) @ "content",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("encoder", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def encoder(
    app: Ariadne,
    group: Group,
    message: MessageChain,
    source: Source,
    code: RegexResult,
    content: RegexResult,
):
    code = code.result.display.strip().lower()
    if quote := message.get(Quote):
        content = (
            await app.get_message_from_id(quote[0].id)
        ).message_chain.display.strip()
    elif content.matched:
        content = message.display[7 + len(code) :].strip()
    else:
        return await app.send_group_message(
            group,
            MessageChain("未指定内容！可以发送 `encode 编码 content` 或对要编码的内容回复 `encode 编码` !"),
            quote=source,
        )
    if code in SPECIAL_TYPE:
        return (
            await app.send_group_message(
                group, MessageChain(f"编码 <{code}> 不支持方法 encode！"), quote=source
            )
            if "encode" not in SPECIAL_TYPE[code]
            else await app.send_group_message(
                group,
                MessageChain(SPECIAL_TYPE[code]["encode"](content)),
                quote=source,
            )
        )

    try:
        return await app.send_group_message(
            group, MessageChain(content.encode().decode(code)), quote=source
        )
    except LookupError:
        return await app.send_group_message(
            group, MessageChain(f"未知的编码： <{code}>"), quote=source
        )
    except Exception as e:
        return await app.send_group_message(
            group, MessageChain(f"发生错误：{str(e)}"), quote=source
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    FullMatch("decode").space(SpacePolicy.FORCE),
                    RegexMatch(r"[\S]+").help("要转换的编码") @ "code",
                    WildcardMatch(optional=True) @ "content",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("decoder", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def decoder(
    app: Ariadne,
    group: Group,
    message: MessageChain,
    source: Source,
    code: RegexResult,
    content: RegexResult,
):
    code = code.result.display.strip().lower()
    if quote := message.get(Quote):
        content = (
            await app.get_message_from_id(quote[0].id)
        ).message_chain.display.strip()
    elif content.matched:
        content = message.display[7 + len(code) :].strip()
    else:
        return await app.send_group_message(
            group,
            MessageChain("未指定内容！可以发送 `decode 编码 content` 或对要编码的内容回复 `decode 编码` !"),
            quote=source,
        )
    if code not in SPECIAL_TYPE:
        # try:
        #     return await app.send_group_message(group, MessageChain(content.encode().decode(code)), quote=source)
        # except LookupError:
        #     return await app.send_group_message(group, MessageChain(f"未知的编码： <{code}>"), quote=source)
        # except Exception as e:
        #     return await app.send_group_message(group, MessageChain(f"发生错误：{str(e)}"), quote=source)
        return await app.send_group_message(
            group,
            MessageChain(
                f"目前暂支持 {'、'.join([f'<{i}>' for i in SPECIAL_TYPE.keys() if SPECIAL_TYPE[i].get('decode')])} "
                f"的 decode方法！"
            ),
            quote=source,
        )
    if "decode" not in SPECIAL_TYPE[code]:
        return await app.send_group_message(
            group, MessageChain(f"编码 <{code}> 不支持方法 decode！"), quote=source
        )
    try:
        return await app.send_group_message(
            group, MessageChain(SPECIAL_TYPE[code]["decode"](content)), quote=source
        )
    except Exception as e:
        return await app.send_group_message(
            group, MessageChain(f"发生错误：{str(e)}"), quote=source
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    FullMatch("set detect"),
                    WildcardMatch(optional=True) @ "content",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("set_detect", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def set_detect(
    app: Ariadne,
    group: Group,
    message: MessageChain,
    source: Source,
    content: RegexResult,
):
    if quote := message.get(Quote):
        content = (
            (await app.get_message_from_id(quote[0].id))
            .message_chain.display.strip()
            .encode()
        )
    elif content.matched:
        content = message.display[10:].strip().encode()
    else:
        return await app.send_group_message(
            group,
            MessageChain("未指定内容！可以发送 `set detect content` 或对要编码的内容回复 `set detect` !"),
            quote=source,
        )
    data = chardet.detect(content)
    encoding = data["encoding"]
    confidence = data["confidence"]
    await app.send_group_message(
        group, MessageChain(f"推测编码为{encoding}，可信度{confidence}"), quote=source
    )
