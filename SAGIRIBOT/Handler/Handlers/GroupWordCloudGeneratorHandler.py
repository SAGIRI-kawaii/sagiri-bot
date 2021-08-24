import os
import random
import numpy as np
import jieba.analyse

from io import BytesIO
from PIL import Image as IMG
from datetime import datetime
import matplotlib.pyplot as plt
from sqlalchemy import select, func
from dateutil.relativedelta import relativedelta
from wordcloud import WordCloud, ImageColorGenerator

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.ORM.AsyncORM import orm
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.ORM.AsyncORM import ChatRecord, UserCalledCount
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.utils import update_user_call_count_plus1, user_permission_require
from SAGIRIBOT.decorators import frequency_limit_require_weight_free, switch, blacklist


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def group_wordcloud_generator_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await GroupWordCloudGeneratorHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class GroupWordCloudGeneratorHandler(AbstractHandler):
    __name__ = "GroupWordCloudGeneratorHandler"
    __description__ = "群词云生成器"
    __usage__ = "在群中发送 `我的月/年内总结` 即可查看个人月/年词云\n在群众发送 `本群月/年内总结` 即可查看群组月/年词云（需要权限等级2）"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text == "我的月内总结":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return await GroupWordCloudGeneratorHandler.get_review(group, member, "month", "member")
        elif message_text == "我的年内总结":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return await GroupWordCloudGeneratorHandler.get_review(group, member, "year", "member")
        elif message_text == "本群月内总结":
            if await user_permission_require(group, member, 2):
                await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
                return await GroupWordCloudGeneratorHandler.get_review(group, member, "month", "group")
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足呢~爪巴!")]), QuoteSource(GroupStrategy()))
        elif message_text == "本群年内总结":
            if await user_permission_require(group, member, 2):
                await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
                return await GroupWordCloudGeneratorHandler.get_review(group, member, "year", "group")
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足呢~爪巴!")]), QuoteSource(GroupStrategy()))
        else:
            return None

    @staticmethod
    async def count_words(sp, n):
        w = {}
        for i in sp:
            if i not in w:
                w[i] = 1
            else:
                w[i] += 1
        top = sorted(w.items(), key=lambda item: (-item[1], item[0]))
        top_n = top[:n]
        return top_n

    @staticmethod
    async def filter_label(label_list: list) -> list:
        not_filter = ["草"]
        filter_list = ["jpg", "png", "img-", '{', '}', '<', '>', "url", "pid", "p0", "www", ":/", "qq"]
        image_filter = "mirai:"
        result = []
        for i in label_list:
            if image_filter in i:
                continue
            if i.isdigit():
                continue
            if any([word in i for word in filter_list]):
                continue
            elif i in not_filter:
                result.append(i)
            elif len(i) != 1 and i.find('nbsp') < 0:
                result.append(i)
        return result

    @staticmethod
    async def draw_word_cloud(read_name) -> bytes:

        def random_pic(base_path: str) -> str:
            path_dir = os.listdir(base_path)
            path = random.sample(path_dir, 1)[0]
            return base_path + path

        mask = np.array(IMG.open(random_pic(f'statics/wordcloud/')))
        # print(mask.shape)
        wc = WordCloud(
            font_path=f'statics/fonts/STKAITI.TTF',
            background_color='white',
            # max_words=500,
            max_font_size=100,
            width=1920,
            height=1080,
            mask=mask
        )
        name = []
        value = []
        for t in read_name:
            name.append(t[0])
            value.append(t[1])
        for i in range(len(name)):
            name[i] = str(name[i])
        dic = dict(zip(name, value))
        # print(dic)
        # print(len(dic.keys()))
        wc.generate_from_frequencies(dic)
        image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
        # print(image_colors.image.shape)
        wc.recolor(color_func=image_colors)
        plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
        plt.axis("off")
        bytes_io = BytesIO()
        img = wc.to_image()
        img.save(bytes_io, format='PNG')
        return bytes_io.getvalue()

    @staticmethod
    @frequency_limit_require_weight_free(3)
    async def get_review(group: Group, member: Member, review_type: str, target: str) -> MessageItem:
        group_id = group.id
        member_id = member.id
        time = datetime.now()
        time_right = time.strftime("%Y-%m-%d %H:%M:%S")
        if review_type == "year":
            timep = time - relativedelta(years=1)
            time_left = (time - relativedelta(years=1)).strftime("%Y-%m-%d %H:%M:%S")
            tag = "年内"
        elif review_type == "month":
            timep = time - relativedelta(months=1)
            time_left = (time - relativedelta(years=1)).strftime("%Y-%m-%d %H:%M:%S")
            tag = "月内"
        else:
            return MessageItem(MessageChain.create([Plain(text="Error: review_type invalid!")]), QuoteSource(GroupStrategy()))

        sql = select(
            ChatRecord.id,
            ChatRecord.time,
            ChatRecord.group_id,
            ChatRecord.member_id,
            ChatRecord.content,
            ChatRecord.seg
        ).where(
            ChatRecord.group_id == group_id,
            ChatRecord.member_id == member_id if target == "member" else True,
            ChatRecord.time < time,
            ChatRecord.time > timep
        )

        if not (res := list(await orm.fetchall(sql))):
            return MessageItem(MessageChain.create([Plain(text="没有你的发言记录呐~")]), QuoteSource(GroupStrategy()))
        texts = []
        for i in res:
            if i[5]:
                texts += await GroupWordCloudGeneratorHandler.filter_label(i[5].split("|"))
            else:
                texts.append(i[4])
        # top_n = await GroupWordCloudGeneratorHandler.count_words(texts, 20000)
        sql = select([func.count()]).select_from(
            ChatRecord
        ).where(
            ChatRecord.group_id == group_id,
            ChatRecord.member_id == member_id if target == "member" else True,
            ChatRecord.time < time,
            ChatRecord.time > timep
        )
        if not (res := list(await orm.fetchone(sql))):
            return MessageItem(MessageChain.create([Plain(text="没有你的发言记录呐~")]), QuoteSource(GroupStrategy()))

        times = res[0]
        return MessageItem(
            MessageChain.create([
                Plain(text="记录时间：\n"),
                Plain(text=f"{time_left}"),
                Plain(text="\n---------至---------\n"),
                Plain(text=f"{time_right}"),
                Plain(
                    text=f"\n自有记录以来，{'你' if target == 'member' else '本群'}一共发了{times}条消息\n下面是{'你的' if target == 'member' else '本群的'}{tag}词云:\n"),
                Image.fromUnsafeBytes(await GroupWordCloudGeneratorHandler.draw_word_cloud(jieba.analyse.extract_tags(" ".join(texts), topK=1000, withWeight=True, allowPOS=())))
            ]),
            QuoteSource(GroupStrategy())
        )


class TfIdf:
    def __init__(self):
        self.weighted = False
        self.documents = []
        self.corpus_dict = {}

    def add_document(self, doc_name, list_of_words):
        doc_dict = {}
        for w in list_of_words:
            doc_dict[w] = doc_dict.get(w, 0.) + 1.0
            self.corpus_dict[w] = self.corpus_dict.get(w, 0.0) + 1.0

        length = float(len(list_of_words))
        for k in doc_dict:
            doc_dict[k] = doc_dict[k] / length

        self.documents.append([doc_name, doc_dict])

    def similarities(self, list_of_words):
        query_dict = {}
        for w in list_of_words:
            query_dict[w] = query_dict.get(w, 0.0) + 1.0

        length = float(len(list_of_words))
        for k in query_dict:
            query_dict[k] = query_dict[k] / length

        sims = []
        for doc in self.documents:
            score = 0.0
            doc_dict = doc[1]
            for k in query_dict:
                if k in doc_dict:
                    score += (query_dict[k] / self.corpus_dict[k]) + (
                      doc_dict[k] / self.corpus_dict[k])
            sims.append([doc[0], score])

        return sims

    def save(self):
        pass

    def load(self):
        pass
