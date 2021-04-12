import re

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.MessageSender.Strategy import Normal, GroupStrategy, QuoteSource


class StatusPresenterHandler(AbstractHandler):
    __name__ = "StatusPresenterHandler"
    __description__ = "一个bot状态显示Handler"
    __usage__ = "在群中发送 `/chains` 即可查看当前职责链顺序\n在群中发送 `/help` 即可查看Handler编号\n在群中发送 `/help 编号` 即可查看当前Handler使用方法"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text == "/chains":
            app_core = AppCore.get_core_instance()
            return MessageItem(
                MessageChain.create([Plain(text="目前链序：\n    " + "\n    ".join([handler.__name__ for handler in app_core.get_group_chain()]))]),
                Normal(GroupStrategy())
            )
        elif message_text == "/help":
            app_core = AppCore.get_core_instance()
            content = "目前已加载Handler：\n"
            index = 0
            for handler in app_core.get_group_chain():
                index = index + 1
                content += f"{index}. {handler.__name__}\n"
            content += "请回复 /help 序号来查看Handler描述"
            return MessageItem(
                MessageChain.create([Plain(text=content)]),
                QuoteSource(GroupStrategy())
            )
        elif re.match(r"/help [0-9]+", message_text):
            chains = AppCore.get_core_instance().get_group_chain()
            length = len(chains)
            index = int(message_text[6:])
            if index > length:
                return MessageItem(MessageChain.create([Plain(text="非法编号！请检查发送的信息！")]), QuoteSource(GroupStrategy()))
            else:
                content = "Handler详情：\n"
                handler = chains[index - 1]
                content += f"名称：{handler.__name__}\n"
                content += f"描述：{handler.__description__}\n"
                content += f"使用方法：{handler.__usage__}"
            return MessageItem(MessageChain.create([Plain(text=content)]), QuoteSource(GroupStrategy()))
        else:
            return await super().handle(app, message, group, member)
