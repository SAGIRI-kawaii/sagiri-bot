import re

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import WildcardMatch, FullMatch, RegexResult

from utils.text_engine.adapter import GraiaAdapter
from utils.text_engine.text_engine import TextEngine
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("MessageMerger")
channel.author("SAGIRI-kawaii")
channel.description("将收到的消息合并为图片，在群中发送 `/merge 文字/图片`")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/merge"), WildcardMatch().flags(re.S) @ "msg_to_merge"])],
        decorators=[
            FrequencyLimit.require("message_merger", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def message_merger(app: Ariadne, message: MessageChain, group: Group, msg_to_merge: RegexResult):
    await app.sendGroupMessage(
        group,
        MessageChain([Image(
            data_bytes=TextEngine([GraiaAdapter(msg_to_merge.result)], min_width=1080).draw()
        )]),
        quote=message.getFirst(Source)
    )
