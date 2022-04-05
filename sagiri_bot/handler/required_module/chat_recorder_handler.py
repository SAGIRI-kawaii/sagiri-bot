import re
import jieba
import datetime

from graia.saya import Saya, Channel
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.control import UserCalledCountControl
from sagiri_bot.utils import update_user_call_count_plus
from sagiri_bot.orm.async_orm import UserCalledCount, ChatRecord

saya = Saya.current()
channel = Channel.current()

channel.name("ChatRecorder")
channel.author("SAGIRI-kawaii")
channel.description("一个记录聊天记录的插件，可配合词云等插件使用")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[UserCalledCountControl.add(UserCalledCountControl.CHAT)]
    )
)
async def chat_record(message: MessageChain, group: Group, member: Member):
    content = "".join([plain.text for plain in message.get(Plain)]).strip()
    filter_words = re.findall(r"\[mirai:(.*?)\]", content, re.S)
    for i in filter_words:
        content = content.replace(f"[mirai:{i}]", "")
    seg_result = jieba.lcut(content) if content else ''
    await orm.add(
        ChatRecord,
        {
            "time": datetime.datetime.now(),
            "group_id": group.id,
            "member_id": member.id,
            "persistent_string": message.asPersistentString(),
            "seg": "|".join(seg_result) if seg_result else ''
        }
    )
