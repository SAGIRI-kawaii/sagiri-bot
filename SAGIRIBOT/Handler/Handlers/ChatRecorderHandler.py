import re
import jieba
# import pkuseg
import traceback
import datetime
from loguru import logger

from sqlalchemy.sql import select, desc
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.ORM.Tables import ChatRecord, UserCalledCount


class ChatRecordHandler(AbstractHandler):
    """
    聊天记录Handler
    """
    __seg = None
    __name__ = "ChatRecordHandler"
    __description__ = "一个记录聊天记录的Handler"
    __usage__ = "自动触发"

    def __init__(self):
        super().__init__()
        # self.__seg = pkuseg.pkuseg()

    async def record(self, message: MessageChain, group: Group, member: Member):
        await update_user_call_count_plus1(group, member, UserCalledCount.chat_count, "chat_count")
        content = "".join([plain.text for plain in message.get(Plain)])
        filter_words = re.findall(r"\[mirai:(.*?)\]", content, re.S)
        for i in filter_words:
            content = content.replace(f"[mirai:{i}]", "")
        if content:
            seg_result = jieba.lcut(content)
            if not seg_result:
                return None
            new_id = list(orm.fetchone(select(ChatRecord.id).order_by(desc(ChatRecord.id)), 1))
            new_id = new_id[0][0] + 1 if new_id else 1
            try:
                orm.add(
                    ChatRecord,
                    {
                        "id": new_id,
                        "time": datetime.datetime.now(),
                        "group_id": group.id,
                        "member_id": member.id,
                        "content": content,
                        "seg": "|".join(seg_result)
                    }
                )
            except Exception as e:
                logger.error(traceback.format_exc())
                orm.session.rollback()

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        await self.record(message, group, member)
        # return await super().handle(app, message, group, member)
