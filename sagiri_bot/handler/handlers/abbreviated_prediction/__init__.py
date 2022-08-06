import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne

from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from sagiri_bot.internal_utils import get_command
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("AbbreviatedPrediction")
channel.author("SAGIRI-kawaii")
channel.description("一个获取英文缩写意思的插件，在群中发送 `缩 内容` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r"[A-Za-z0-9]+").help("要缩写的内容") @ "content"]
            )
        ],
        decorators=[
            FrequencyLimit.require("abbreviated_prediction", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def abbreviated_prediction(app: Ariadne, group: Group, source: Source, content: RegexResult):
    url = "https://lab.magiconch.com/api/nbnhhsh/guess"
    headers = {"referer": "https://lab.magiconch.com/nbnhhsh/"}
    data = {"text": content.result.display}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=data) as resp:
            res = await resp.json()

    result = "可能的结果:\n\n"
    has_result = False
    for i in res:
        if "trans" in i and i["trans"]:
            has_result = True
            result += f"{i['name']} => {'，'.join(i['trans'])}\n\n"
        elif "trans" in i or not i["inputting"]:
            result += f"{i['name']} => 没找到结果！\n\n"
        else:
            has_result = True
            result += f"{i['name']} => {'，'.join(i['inputting'])}\n\n"
    result = result if has_result else "没有找到结果哦~"
    await app.send_group_message(group, MessageChain(result), quote=source)
