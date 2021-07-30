from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage
from graia.application.message.elements.internal import Plain, FlashImage

from SAGIRIBOT.utils import get_setting
from SAGIRIBOT.ORM.AsyncORM import Setting
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def flash_image_catcher_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await FlashImageCatcherHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class FlashImageCatcherHandler(AbstractHandler):
    __name__ = "FlashImageCatcherHandler"
    __description__ = "闪照转换Handler"
    __usage__ = "发送闪照自动转换"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.has(FlashImage) and await get_setting(group.id, Setting.anti_flashimage):
            return MessageItem(
                MessageChain.create([Plain(text="FlashImage => Image\n"), message[FlashImage][0].asNormal()]),
                Normal(GroupStrategy())
            )
