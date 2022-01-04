import re
import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.utils import get_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.strategy import QuoteSource, Normal
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount
from sagiri_bot.decorators import frequency_limit_require_weight_free, switch, blacklist

saya = Saya.current()
channel = Channel.current()

channel.name("NetworkCompiler")
channel.author("SAGIRI-kawaii")
channel.description("一个网络编译器插件，在群中发送 `super language\\n code`即可")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def network_compiler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await NetworkCompiler.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class NetworkCompiler(AbstractHandler):
    __name__ = "NetworkCompiler"
    __description__ = "一个网络编译器插件"
    __usage__ = "在群中发送 `super language\\ncode`即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if re.match(r"super .*[\n\r]+[\s\S]*", message_text):
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            if not await get_setting(group.id, Setting.compile):
                return MessageItem(MessageChain.create([Plain(text="网络编译器功能关闭了呐~去联系管理员开启吧~")]), Normal())
            language = re.findall(r"super (.*?)[\n\r]+[\s\S]*", message_text, re.S)[0]
            code = message_text[7 + len(language):]
            result = await NetworkCompiler.network_compiler(group, member, language, code)
            if isinstance(result, str):
                return MessageItem(MessageChain.create([Plain(text=result)]), QuoteSource())
            else:
                return MessageItem(
                    MessageChain.create([Plain(text=result["output"] if result["output"] else result["errors"])]),
                    QuoteSource()
                )
        else:
            return None

    @staticmethod
    @frequency_limit_require_weight_free(2)
    async def network_compiler(group: Group, member: Member, language: str, code: str):
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
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=payload) as resp:
                res = await resp.json()
        return {
            "output": res["output"],
            "errors": res["errors"]
        }
