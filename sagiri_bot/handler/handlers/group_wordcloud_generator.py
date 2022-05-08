import os
import random
from datetime import datetime
from io import BytesIO

import jieba.analyse
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as IMG
from dateutil.relativedelta import relativedelta
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Source
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    FullMatch,
    MatchResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from sqlalchemy import select, func
from wordcloud import WordCloud, ImageColorGenerator

from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)
from sagiri_bot.orm.async_orm import ChatRecord
from sagiri_bot.orm.async_orm import orm
from sagiri_bot.utils import user_permission_require

saya = Saya.current()
channel = Channel.current()

channel.name("GroupWordCloudGenerator")
channel.author("SAGIRI-kawaii")
channel.description("群词云生成器，" "在群中发送 `[我的|本群][日|月|年]内总结` 即可查看个人/群 月/年词云（群词云需要权限等级2）")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch("我的", "本群") @ "scope",
                    UnionMatch("年内", "月内", "日内") @ "period",
                    FullMatch("总结"),
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require(channel.meta["name"], 3),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def group_wordcloud_generator(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    scope: MatchResult,
    period: MatchResult,
):
    scope = "group" if scope.result.asDisplay() == "本群" else "member"
    if scope == "group" and not await user_permission_require(group, member, 2):
        return await app.sendGroupMessage(
            group,
            MessageChain.create([Plain(text="权限不足呢~爪巴!")]),
            quote=message.getFirst(Source),
        )

    period = period.result.asDisplay()
    await app.sendGroupMessage(
        group,
        await GroupWordCloudGenerator.get_review(group, member, period, scope),
        quote=message.getFirst(Source),
    )


class GroupWordCloudGenerator:
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
        filter_list = [
            "jpg",
            "png",
            "img-",
            "{",
            "}",
            "<",
            ">",
            "url",
            "pid",
            "p0",
            "www",
            ":/",
            "qq",
        ]
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
            elif len(i) != 1 and i.find("nbsp") < 0:
                result.append(i)
        return result

    @staticmethod
    async def draw_word_cloud(read_name) -> bytes:
        def random_pic(base_path: str) -> str:
            path_dir = os.listdir(base_path)
            path = random.sample(path_dir, 1)[0]
            return base_path + path

        mask = np.array(IMG.open(random_pic(f"statics/wordcloud/")))
        wc = WordCloud(
            font_path=f"statics/fonts/STKAITI.TTF",
            background_color="white",
            max_font_size=100,
            width=1920,
            height=1080,
            mask=mask,
        )
        name = []
        value = []
        for t in read_name:
            name.append(t[0])
            value.append(t[1])
        for i in range(len(name)):
            name[i] = str(name[i])
        dic = dict(zip(name, value))
        wc.generate_from_frequencies(dic)
        image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
        wc.recolor(color_func=image_colors)
        plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
        plt.axis("off")
        bytes_io = BytesIO()
        img = wc.to_image()
        img.save(bytes_io, format="PNG")
        return bytes_io.getvalue()

    @staticmethod
    async def get_review(
        group: Group, member: Member, review_type: str, target: str
    ) -> MessageChain:
        group_id = group.id
        member_id = member.id
        time = datetime.now()
        time_right = time.strftime("%Y-%m-%d %H:%M:%S")
        if review_type == "年内":
            timep = time - relativedelta(years=1)
            time_left = (time - relativedelta(years=1)).strftime("%Y-%m-%d %H:%M:%S")
        elif review_type == "月内":
            timep = time - relativedelta(months=1)
            time_left = (time - relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            timep = time - relativedelta(days=1)
            time_left = (time - relativedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        sql = select(
            ChatRecord.id,
            ChatRecord.time,
            ChatRecord.group_id,
            ChatRecord.member_id,
            ChatRecord.seg,
        ).where(
            ChatRecord.group_id == group_id,
            ChatRecord.member_id == member_id if target == "member" else True,
            ChatRecord.time < time,
            ChatRecord.time > timep,
        )

        if not (res := list(await orm.fetchall(sql))):
            return MessageChain.create([Plain(text="没有你的发言记录呐~")])
        texts = []
        for i in res:
            if i[4]:
                texts += await GroupWordCloudGenerator.filter_label(i[4].split("|"))
        sql = (
            select([func.count()])
            .select_from(ChatRecord)
            .where(
                ChatRecord.group_id == group_id,
                ChatRecord.member_id == member_id if target == "member" else True,
                ChatRecord.time < time,
                ChatRecord.time > timep,
            )
        )
        if not (res := list(await orm.fetchone(sql))):
            return MessageChain.create([Plain(text="没有你的发言记录呐~")])

        times = res[0]
        return MessageChain.create(
            [
                Plain(text="记录时间：\n"),
                Plain(text=f"{time_left}"),
                Plain(text="\n---------至---------\n"),
                Plain(text=f"{time_right}"),
                Plain(
                    text="\n自有记录以来，"
                    f"{'你' if target == 'member' else '本群'}"
                    f"一共发了{times}条消息\n下面是"
                    f"{'你的' if target == 'member' else '本群的'}"
                    f"{review_type}词云:\n"
                ),
                Image(
                    data_bytes=await GroupWordCloudGenerator.draw_word_cloud(
                        jieba.analyse.extract_tags(
                            " ".join(texts), topK=1000, withWeight=True, allowPOS=()
                        )
                    )
                ),
            ]
        )


class TfIdf:
    def __init__(self):
        self.weighted = False
        self.documents = []
        self.corpus_dict = {}

    def add_document(self, doc_name, list_of_words):
        doc_dict = {}
        for w in list_of_words:
            doc_dict[w] = doc_dict.get(w, 0.0) + 1.0
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
                        doc_dict[k] / self.corpus_dict[k]
                    )
            sims.append([doc[0], score])

        return sims

    def save(self):
        pass

    def load(self):
        pass
