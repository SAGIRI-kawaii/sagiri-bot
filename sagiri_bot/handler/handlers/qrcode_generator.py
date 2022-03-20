import qrcode
from io import BytesIO

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()

channel.name("QrcodeGenerator")
channel.author("SAGIRI-kawaii")
channel.description("一个生成二维码的插件，在群中发送 `qrcode 内容` 即可（文字）")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("qrcode"), RegexMatch(r"[^/s]+$") @ "content"])],
        decorators=[
            FrequencyLimit.require("qrcode_generator", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def qrcode_generator(app: Ariadne, message: MessageChain, group: Group, content: RegexResult):
    content = content.result.asDisplay()
    qrcode_img = qrcode.make(content)
    bytes_io = BytesIO()
    qrcode_img.save(bytes_io)
    await app.sendGroupMessage(
        group,
        MessageChain([Image(data_bytes=bytes_io.getvalue())]),
        quote=message.getFirst(Source)
    )
