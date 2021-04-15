import aiohttp

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import Normal, GroupStrategy
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount


class TodayInHistoryHandler(AbstractHandler):
    """ 历史上的今天Handler """
    __name__ = "TodayInHistoryHandler"
    __description__ = "一个获取历史上的今天的Handler"
    __usage__ = "在群中发送 `历史上的今天` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "历史上的今天":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_today_in_history(group, member))
            # return await self.get_today_in_history(group, member)
        else:
            return None
            # return await super().handle(app, message, group, member)

    @staticmethod
    @frequency_limit_require_weight_free(1)
    async def get_today_in_history(group: Group, member: Member) -> MessageItem:
        api_url = "https://api.sagiri-web.com/historyToday/"

        async with aiohttp.ClientSession() as session:
            async with session.get(url=api_url) as resp:
                text = await resp.text()

        text = text.replace("\\n", "\n")
        text = text[1:-1]
        while len(text) > 400:
            text = "\n".join(text.split("\n")[int(len(text.split("\n")) / 2):])
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal(GroupStrategy()))
