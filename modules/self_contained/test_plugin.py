from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, GroupMessage, Member

from shared.utils.text2image import md2pic
from shared.models.config import GlobalConfig
from shared.utils.control import Distribute

saya = create(Saya)
channel = Channel.current()

channel.name("Test")
channel.author("SAGIRI-kawaii")
config = create(GlobalConfig)


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[Distribute.distribute()]))
async def _(app: Ariadne, member: Member, group: Group, message: MessageChain, source: Source):
    if message.display.startswith("md:"):
        return await app.send_group_message(group, MessageChain(Image(data_bytes=await md2pic(message.display[3:]))))
    if member.id != config.host_qq:
        return
