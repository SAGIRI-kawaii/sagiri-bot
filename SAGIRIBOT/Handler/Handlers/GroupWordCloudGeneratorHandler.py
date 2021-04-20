import numpy as np
from io import BytesIO
from PIL import Image as IMG
from datetime import datetime
from sqlalchemy import select, func
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from wordcloud import WordCloud, ImageColorGenerator

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image

from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.ORM.Tables import ChatRecord, UserCalledCount
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource


class GroupWordCloudGeneratorHandler(AbstractHandler):
    __name__ = "GroupWordCloudGeneratorHandler"
    __description__ = "群词云生成器"
    __usage__ = "在群中发送 `我的月/年内总结` 即可查看个人月/年词云\n在群众发送 `本群月/年内总结` 即可查看群组月/年词云（需要权限等级2）"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if message_text == "我的月内总结":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_review(group, member, "month", "member"))
        elif message_text == "我的年内总结":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_review(group, member, "year", "member"))
        elif message_text == "本群月内总结":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_review(group, member, "month", "group"))
        elif message_text == "本群年内总结":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            set_result(message, await self.get_review(group, member, "year", "group"))
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
        image_filter = "mirai:"
        result = []
        for i in label_list:
            if image_filter in i:
                continue
            elif i in not_filter:
                result.append(i)
            elif len(i) != 1 and i.find('nbsp') < 0:
                result.append(i)
        return result

    @staticmethod
    async def draw_word_cloud(read_name) -> bytes:
        mask = np.array(IMG.open(f'statics/wordCloud/back.jpg'))
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
            ChatRecord
        ).where(
            ChatRecord.group_id == group_id,
            ChatRecord.member_id == member_id if target == "member" else True,
            ChatRecord.time < time,
            ChatRecord.time > timep
        )

        if not (res := list(orm.fetchall(sql))):
            return MessageItem(MessageChain.create([Plain(text="没有你的发言记录呐~")]), QuoteSource(GroupStrategy()))
        texts = []
        for i in res:
            if i[5]:
                texts += i[5].split("|")
            else:
                texts.append(i[3])
        top_n = await GroupWordCloudGeneratorHandler.count_words(texts, 20000)

        sql = select([func.count()]).select_from(
            ChatRecord
        ).where(
            ChatRecord.group_id == group_id,
            ChatRecord.member_id == member_id if target == "member" else True,
            ChatRecord.time < time,
            ChatRecord.time > timep
        )
        if not (res := list(orm.fetchone(sql))):
            return MessageItem(MessageChain.create([Plain(text="没有你的发言记录呐~")]), QuoteSource(GroupStrategy()))

        times = res[0][0]
        return MessageItem(
            MessageChain.create([
                Plain(text="记录时间：\n"),
                Plain(text=f"{time_left}"),
                Plain(text="\n---------至---------\n"),
                Plain(text=f"{time_right}"),
                Plain(
                    text=f"\n自有记录以来，{'你' if target == 'member' else '本群'}一共发了{times}条消息\n下面是{'你的' if target == 'member' else '本群的'}{tag}词云:\n"),
                Image.fromUnsafeBytes(await GroupWordCloudGeneratorHandler.draw_word_cloud(top_n))
            ]),
            QuoteSource(GroupStrategy())
        )
