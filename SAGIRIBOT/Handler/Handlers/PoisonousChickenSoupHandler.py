import aiohttp

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.utils import get_config
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def poisonous_chicken_soup_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await PoisonousChickenSoupHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class PoisonousChickenSoupHandler(AbstractHandler):
    __name__ = "PoisonousChickenSoupHandler"
    __description__ = "一个获取毒鸡汤的Hanlder"
    __usage__ = "在群中发送 `鸡汤/毒鸡汤/来碗鸡汤` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() in ["来碗鸡汤", "鸡汤", "毒鸡汤"]:
            return await PoisonousChickenSoupHandler.get_soup()
        else:
            return None

    @staticmethod
    async def get_soup():
        url = f"https://du.shadiao.app/api.php?from={get_config('shadiaoAppName')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                text = await resp.text()
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal(GroupStrategy()))
