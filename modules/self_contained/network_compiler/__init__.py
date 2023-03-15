import aiohttp
import asyncio

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.exception import MessageTooLong
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

channel = Channel.current()
channel.name("NetworkCompiler")
channel.author("SAGIRI-kawaii")
channel.description("一个网络编译器插件，在群中发送 `super language\\n code`即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r"[^\s]+") @ "language",
                RegexMatch(r"[\s]+", optional=True),
                RegexMatch(r"[\s\S]+") @ "code",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("network_compiler", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def network_compiler(app: Ariadne, group: Group, source: Source, language: RegexResult, code: RegexResult):
    language = language.result.display
    code = code.result.display
    result = await get_result(language, code)
    if isinstance(result, str):
        await app.send_group_message(group, MessageChain(result), quote=source)
    else:
        try:
            await app.send_group_message(
                group,
                MessageChain(result["output"] if result["output"] else result["errors"]),
                quote=source,
            )
        except MessageTooLong:
            await app.send_group_message(group, MessageChain("MessageTooLong"), quote=source)


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
        "php": 3,
    }
    if language not in legal_language:
        return f"支持的语言：{', '.join(list(legal_language.keys()))}"
    url = "https://tool.runoob.com/compile2.php"
    payload = {
        "code": code,
        "token": "b6365362a90ac2ac7098ba52c13e352b",
        "stdin": "",
        "language": legal_language[language],
        "fileext": language,
    }
    headers = {
        "Host": "tool.runoob.com",
        "Origin": "https://c.runoob.com",
        "Referer": "https://c.runoob.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/87.0.4280.141 Safari/537.36 "
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=payload, timeout=10) as resp:
                res = await resp.json()
    except asyncio.TimeoutError:
        return {"output": "", "errors": "Network Time Limit Exceeded"}
    return {"output": res["output"], "errors": res["errors"]}
