import datetime
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image as IMG
from wordcloud import WordCloud, ImageColorGenerator

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


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


async def draw_word_cloud(read_name):
    image = IMG.open('./statics/back.jpg')
    mask = np.array(image)
    wc = WordCloud(font_path='./statics/simsun.ttc', background_color='White', max_words=500, width=1280, height=720, mask=mask)
    # , mask=mask
    name = []
    value = []
    for t in read_name:
        name.append(t[0])
        value.append(t[1])
    for i in range(len(name)):
        name[i] = str(name[i])
        # name[i] = name[i].encode('gb2312').decode('gb2312')
    dic = dict(zip(name, value))
    print(dic)

    wc.generate_from_frequencies(dic)
    # image_color = ImageColorGenerator(mask)
    plt.imshow(wc)
    plt.axis("off")
    # plt.show()
    wc.to_file('./statics/tempWordCloud.png')


async def get_personal_review(group_id: int, member_id: int, review_type: str) -> list:
    if review_type == "year":
        time = datetime.datetime.now().strftime("%Y")
        sql = f"""SELECT * FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND memberId={member_id} AND time>'{'2020-01-01 00:00:00'}'"""
        # print(sql)
        res = await execute_sql(sql)
        texts = []
        for i in res:
            if i[4]:
                texts += i[4].split(",")
            else:
                texts.append(i[3])
        print(texts)
        top_n = await count_words(texts, 500)
        await draw_word_cloud(top_n)
        sql = f"""SELECT count(*) FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND memberId={member_id} AND time>'{'2020-01-01 00:00:00'}'"""
        res = await execute_sql(sql)
        times = res[0][0]
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=f"时间飞逝，转眼就到了2021年\n自有记录以来，你一共发了{times}条消息\n下面是你的年度词云"),
                Image.fromLocalFile("./statics/tempWordCloud.png")
            ])
        ]
    elif review_type == "month":
        time = datetime.datetime.now().strftime("%Y-%m")
        sql = f"""SELECT * FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND memberId={member_id} AND time>'{time + '-01 00:00:00'}'"""
        print(sql)
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="Error: review_type invalid!")
            ])
        ]


async def get_group_review(group_id: int, member_id: int, review_type: str) -> list:
    if review_type == "year":
        time = datetime.datetime.now().strftime("%Y")
        sql = f"""SELECT * FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND time>'{'2020-01-01 00:00:00'}'"""
        # print(sql)
        res = await execute_sql(sql)
        texts = []
        for i in res:
            if i[4]:
                texts += i[4].split(",")
            else:
                texts.append(i[3])
        print(texts)
        top_n = await count_words(texts, 500)
        await draw_word_cloud(top_n)
        sql = f"""SELECT count(*) FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND time>'{'2020-01-01 00:00:00'}'"""
        res = await execute_sql(sql)
        times = res[0][0]
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=f"时间飞逝，转眼就到了2021年\n自有记录以来，本群一共发了{times}条消息\n下面是本群的年度词云"),
                Image.fromLocalFile("./statics/tempWordCloud.png")
            ])
        ]
    elif review_type == "month":
        time = datetime.datetime.now().strftime("%Y-%m")
        sql = f"""SELECT * FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND time>'{time + '-01 00:00:00'}'"""
        print(sql)
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="Error: review_type invalid!")
            ])
        ]