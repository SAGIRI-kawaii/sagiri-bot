from asyncio.exceptions import TimeoutError

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.element import Source
from graia.ariadne.exception import MessageTooLong
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult

from sagiri_bot.utils import group_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("NetworkCompiler")
channel.author("SAGIRI-kawaii")
channel.description("一个网络编译器插件，在群中发送 `super language\\n code`即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("super"), RegexMatch(r"[^\s]+") @ "language", RegexMatch(r"[\s]+", optional=True),
                RegexMatch(r"[\s\S]+") @ "code"
            ])
        ],
        decorators=[
            FrequencyLimit.require("network_compiler", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def network_compiler(app: Ariadne, message: MessageChain, group: Group, language: RegexResult, code: RegexResult):
    if not await group_setting.get_setting(group.id, Setting.compile):
        await app.sendGroupMessage(group, MessageChain("网络编译器功能关闭了呐~去联系管理员开启吧~"))
        return
    language = language.result.asDisplay()
    code = code.result.asDisplay()
    result = await get_result(language, code)
    if isinstance(result, str):
        await app.sendGroupMessage(group, MessageChain(result), quote=message.getFirst(Source))
    else:
        try:
            await app.sendGroupMessage(
                group,
                MessageChain(result["output"] if result["output"] else result["errors"]),
                quote=message.getFirst(Source)
            )
        except MessageTooLong:
            await app.sendGroupMessage(
                group,
                MessageChain("MessageTooLong"),
                quote=message.getFirst(Source)
            )


async def get_result(language: str, code: str):
    legal_language = {
        "R": 80,
        "vb": 84,
        "ts": 1001,
        "kt": 19,
        "pas": 18,
        "lua": 17,
        "node.js": 4,
        "go": 6,
        "swift": 16,
        "rs": 9,
        "sh": 11,
        "pl": 14,
        "erl": 12,
        "scala": 5,
        "cs": 10,
        "rb": 1,
        "cpp": 7,
        "c": 7,
        "java": 8,
        "py3": 15,
        "py": 0,
        "php": 3
    }
    if language not in legal_language:
        return f"支持的语言：{', '.join(list(legal_language.keys()))}"
    url = "https://tool.runoob.com/compile2.php"
    payload = {
        "code": code,
        "token": "4381fe197827ec87cbac9552f14ec62a",
        "stdin": "",
        "language": legal_language[language],
        "fileext": language
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/87.0.4280.141 Safari/537.36 "
    }
    try:
        async with get_running(Adapter).session.post(url=url, headers=headers, data=payload, timeout=3) as resp:
            res = await resp.json()
    except TimeoutError:
        return {
            "output": "",
            "errors": "Network Time Limit Exceeded"
        }
    return {
        "output": res["output"],
        "errors": res["errors"]
    }
