from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain, Source, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, GroupMessage, Member

from shared.models.config import GlobalConfig
from shared.utils.control import Distribute
from shared.utils.text2img import md2img

saya = create(Saya)
channel = Channel.current()

channel.name("Test")
channel.author("SAGIRI-kawaii")
config = create(GlobalConfig)


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[Distribute.distribute()]))
async def _(app: Ariadne, member: Member, group: Group, message: MessageChain, source: Source):
    if member.id != config.host_qq:
        return
    if message.display.startswith("md:"):
        print("get")
        return await app.send_group_message(group, MessageChain(Image(data_bytes=await md2img(message.display[3:]))))
