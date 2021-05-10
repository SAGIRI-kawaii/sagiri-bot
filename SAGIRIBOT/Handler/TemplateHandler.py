from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.decorators import frequency_limit_require_weight_free


class TemplateHandler(AbstractHandler):
    __name__ = "TemplateHandler"
    __description__ = "Handler示例"
    __usage__ = "None"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        expression = None
        if expression:
            set_result(origin_message=message, item=MessageItem(MessageChain.create([Plain(text="模板")]), Normal(GroupStrategy())))
        else:
            return None




from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await BiliBiliBangumiScheduleHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)
