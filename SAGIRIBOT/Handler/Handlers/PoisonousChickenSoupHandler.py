import aiohttp

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image

from SAGIRIBOT.utils import get_config
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal


class PoisonousChickenSoupHandler(AbstractHandler):
    __name__ = "PoisonousChickenSoupHandler"
    __description__ = "一个获取毒鸡汤的Hanlder"
    __usage__ = "在群中发送 `鸡汤/毒鸡汤/来碗鸡汤` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() in ["来碗鸡汤", "鸡汤", "毒鸡汤"]:
            set_result(message, await self.get_soup())
        else:
            return None

    @staticmethod
    async def get_soup():
        url = f"https://du.shadiao.app/api.php?from={get_config('shadiaoAppName')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                text = await resp.text()
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal(GroupStrategy()))
