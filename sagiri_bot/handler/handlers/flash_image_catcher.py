from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, FlashImage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.utils import get_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("FlashImageCatcher")
channel.author("SAGIRI-kawaii")
channel.description("闪照转换插件，发送闪照自动转换")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def flash_image_catcher(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await FlashImageCatcherHandler.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class FlashImageCatcherHandler(AbstractHandler):
    __name__ = "FlashImageCatcher"
    __description__ = "闪照转换插件"
    __usage__ = "发送闪照自动转换"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.has(FlashImage) and await get_setting(group.id, Setting.anti_flash_image):
            return MessageItem(
                MessageChain.create([Plain(text="FlashImage => Image\n"), message[FlashImage][0].toImage()]),
                Normal()
            )
