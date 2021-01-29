# -*- encoding=utf-8 -*-

import datetime
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image as IMG
from wordcloud import WordCloud, ImageColorGenerator
from dateutil.relativedelta import relativedelta

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
    mask = np.array(IMG.open('./statics/back.jpg'))
    print(mask.shape)
    wc = WordCloud(
        font_path='./statics/simsun.ttc',
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
        # name[i] = name[i].encode('gb2312').decode('gb2312')
    dic = dict(zip(name, value))
    print(dic)
    print(len(dic.keys()))
    wc.generate_from_frequencies(dic)
    image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
    print(image_colors.image.shape)
    wc.recolor(color_func=image_colors)
    plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    # plt.imshow(wc)
    plt.axis("off")
    # plt.show()
    wc.to_file('./statics/temp/tempWordCloud.png')


async def get_personal_review(group_id: int, member_id: int, review_type: str) -> list:
    time = datetime.datetime.now()
    year, month, day, hour, minute, second = time.strftime("%Y %m %d %H %M %S").split(" ")
    if review_type == "year":
        yearp, monthp, dayp, hourp, minutep, secondp = (time - relativedelta(years=1)).strftime("%Y %m %d %H %M %S").split(" ")
        tag = "年内"
    elif review_type == "month":
        yearp, monthp, dayp, hourp, minutep, secondp = (time - relativedelta(months=1)).strftime("%Y %m %d %H %M %S").split(" ")
        tag = "月内"
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="Error: review_type invalid!")
            ])
        ]

    sql = f"""SELECT * FROM chatRecord 
                    WHERE 
                groupId={group_id} AND memberId={member_id} AND time<'{year}-{month}-{day} {hour}:{minute}:{second}'
                                                AND time>'{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}'"""
    # print(sql)
    res = await execute_sql(sql)
    texts = []
    for i in res:
        if i[4]:
            texts += i[4].split(",")
        else:
            texts.append(i[3])
    print(texts)
    top_n = await count_words(texts, 20000)
    await draw_word_cloud(top_n)
    sql = f"""SELECT count(*) FROM chatRecord 
                    WHERE 
                groupId={group_id} AND memberId={member_id} AND time<'{year}-{month}-{day} {hour}:{minute}:{second}'
                                                AND time>'{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}'"""
    res = await execute_sql(sql)
    times = res[0][0]
    return [
        "quoteSource",
        MessageChain.create([
            Plain(text="记录时间：\n"),
            Plain(text=f"{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}"),
            Plain(text="\n---------至---------\n"),
            Plain(text=f"{year}-{month}-{day} {hour}:{minute}:{second}"),
            Plain(text=f"\n自有记录以来，你一共发了{times}条消息\n下面是你的{tag}个人词云:\n"),
            Image.fromLocalFile("./statics/temp/tempWordCloud.png")
        ])
    ]


async def get_group_review(group_id: int, member_id: int, review_type: str) -> list:
    time = datetime.datetime.now()
    year, month, day, hour, minute, second = time.strftime("%Y %m %d %H %M %S").split(" ")
    tag = ""
    if review_type == "year":
        yearp, monthp, dayp, hourp, minutep, secondp = (time - relativedelta(years=1)).strftime("%Y %m %d %H %M %S").split(" ")
        tag = "年内"
    elif review_type == "month":
        yearp, monthp, dayp, hourp, minutep, secondp = (time - relativedelta(months=1)).strftime("%Y %m %d %H %M %S").split(" ")
        tag = "月内"
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="Error: review_type invalid!")
            ])
        ]
    sql = f"""SELECT * FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND time<'{year}-{month}-{day} {hour}:{minute}:{second}'
                                                    AND time>'{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}'"""
    # print(sql)
    res = await execute_sql(sql)
    texts = []
    for i in res:
        if i[4]:
            texts += i[4].split(",")
        else:
            if i[3]:
                texts.append(i[3])
    print(texts)
    top_n = await count_words(texts, 20000)
    await draw_word_cloud(top_n)
    sql = f"""SELECT count(*) FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND time<'{year}-{month}-{day} {hour}:{minute}:{second}'
                                                    AND time>'{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}'"""
    res = await execute_sql(sql)
    times = res[0][0]
    return [
        "None",
        MessageChain.create([
            Plain(text="记录时间：\n"),
            Plain(text=f"{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}"),
            Plain(text="\n---------至---------\n"),
            Plain(text=f"{year}-{month}-{day} {hour}:{minute}:{second}"),
            Plain(text=f"\n自有记录以来，本群一共发了{times}条消息\n下面是本群的{tag}词云:\n"),
            Image.fromLocalFile("./statics/temp/tempWordCloud.png")
        ])
    ]


if __name__ == "__main__":
    test(dic)
