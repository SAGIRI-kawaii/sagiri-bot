import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("PoisonousChickenSoup")
channel.author("SAGIRI-kawaii")
channel.description("一个获取毒鸡汤的插件，在群中发送 `[鸡汤|毒鸡汤|来碗鸡汤]` 即可")

core = AppCore.get_core_instance()
config = core.get_config()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def poisonous_chicken_soup(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await PoisonousChickenSoup.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class PoisonousChickenSoup(AbstractHandler):
    __name__ = "PoisonousChickenSoup"
    __description__ = "一个获取毒鸡汤的插件"
    __usage__ = "在群中发送 `[鸡汤|毒鸡汤|来碗鸡汤]` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() in ["来碗鸡汤", "鸡汤", "毒鸡汤"]:
            return await PoisonousChickenSoup.get_soup()
        else:
            return None

    @staticmethod
    async def get_soup():
        url = f"https://du.shadiao.app/api.php?from={config.functions.get('shadiao_app_name')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                text = await resp.text()
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal())
