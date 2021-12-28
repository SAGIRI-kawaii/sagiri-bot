import re
import jieba
import datetime

import sqlalchemy.exc
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from SAGIRIBOT.ORM.AsyncORM import orm
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.ORM.AsyncORM import UserCalledCount, ChatRecord

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def chat_record_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    await ChatRecordHandler.handle(app, message, group, member)


class ChatRecordHandler(AbstractHandler):
    """
    聊天记录Handler
    """
    __name__ = "ChatRecordHandler"
    __description__ = "一个记录聊天记录的Handler"
    __usage__ = "自动触发"

    @staticmethod
    async def record(message: MessageChain, group: Group, member: Member):
        await update_user_call_count_plus1(group, member, UserCalledCount.chat_count, "chat_count")
        content = "".join([plain.text for plain in message.get(Plain)]).strip()
        filter_words = re.findall(r"\[mirai:(.*?)\]", content, re.S)
        for i in filter_words:
            content = content.replace(f"[mirai:{i}]", "")
        if content:
            seg_result = jieba.lcut(content)
            # dictionary = corpora.Dictionary([seg_result])
            # new_corpus = [dictionary.doc2bow(seg_result)]
            # # if not os.path.exists(f"./statics/model/tf_idf_model.tfidf"):
            # #     os.mknod("./model/statics/tf_idf_model.tfidf")
            # tfidf = models.TfidfModel(models.TfidfModel.load("./statics/model/tf_idf_model.tfidf") + new_corpus)
            # with open(f"./statics/model/tf_idf_model.tfidf", "w") as w:
            #     tfidf.save(w)
            if not seg_result:
                return None
            try:
                await orm.add(
                    ChatRecord,
                    {
                        "time": datetime.datetime.now(),
                        "group_id": group.id,
                        "member_id": member.id,
                        "content": content,
                        "seg": "|".join(seg_result)
                    }
                )
            except sqlalchemy.exc.DataError:
                try:
                    await orm.add(
                        ChatRecord,
                        {
                            "time": datetime.datetime.now(),
                            "group_id": group.id,
                            "member_id": member.id,
                            "content": content[:4000],
                            "seg": ("|".join(seg_result))[:4000]
                        }
                    )
                except Exception:
                    return None

    @staticmethod
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        await ChatRecordHandler.record(message, group, member)


chat_recoder = ChatRecordHandler()
