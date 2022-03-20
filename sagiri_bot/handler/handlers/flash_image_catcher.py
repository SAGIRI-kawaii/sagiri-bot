from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, FlashImage
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.utils import group_setting
from sagiri_bot.orm.async_orm import Setting
saya = Saya.current()
channel = Channel.current()

channel.name("FlashImageCatcher")
channel.author("SAGIRI-kawaii")
channel.description("闪照转换插件，发送闪照自动转换")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def flash_image_catcher(app: Ariadne, message: MessageChain, group: Group):
    if message.has(FlashImage) and await group_setting.get_setting(group.id, Setting.anti_flash_image):
        await app.sendGroupMessage(
            group, MessageChain([Plain(text="FlashImage => Image\n"), message[FlashImage][0].toImage()])
        )
