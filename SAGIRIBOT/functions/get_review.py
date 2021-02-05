# -*- encoding=utf-8 -*-
import aiohttp
import datetime
import numpy as np
import matplotlib.pyplot as plt
import os
from wordcloud import WordCloud, ImageColorGenerator
from dateutil.relativedelta import relativedelta
from PIL import Image as IMG
from io import BytesIO

from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def set_personal_wordcloud_mask(group_id: int, member_id: int, mask: Image) -> list:
    img_url = mask.url
    path = f"./statics/wordCloud/PersonalCustomizationMask/{group_id}_{member_id}.jpg"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=img_url) as resp:
            img_content = await resp.read()
    image = IMG.open(BytesIO(img_content))
    image.save(path)
    return [
        "quoteSource",
        MessageChain.create([
            Plain(text="添加成功！")
        ])
    ]


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


async def draw_word_cloud(read_name, maskpath: str = "./statics/wordCloud/back.jpg"):
    mask = np.array(IMG.open(maskpath))
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
    mask_path = f"./statics/wordCloud/PersonalCustomizationMask/{group_id}_{member_id}.jpg"
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
    if os.path.exists(mask_path):
        await draw_word_cloud(top_n, mask_path)
    else:
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


async def daily_chat_rank(group_id: int, app: GraiaMiraiApplication) -> list:
    time = datetime.datetime.now()
    year, month, day = time.strftime("%Y %m %d").split(" ")
    sql = f"""SELECT memberId, count(memberId) FROM chatRecord 
                        WHERE 
                    groupId={group_id} AND time>='{year}-{month}-{day} 00:00:00' AND memberId!=80000000
                        GROUP BY memberId ORDER BY count(memberId) desc"""
    # print(sql)
    res = await execute_sql(sql)
    res = res[:10]
    # print(res)
    plt.rcdefaults()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    name = []
    for data in res:
        if member := await app.getMember(group_id, data[0]):
            name.append(member.name)
        else:
            name.append("NameNullError!")
    # name = [(await app.getMember(group_id, member[0])).name for member in res]
    count = [data[1] for data in res]
    print(name)
    print(count)
    plt.barh(range(len(count)), count, tick_label=name)
    plt.title(f"群{(await app.getGroup(group_id)).name}今日发言前十（截至目前）")
    plt.tight_layout()
    plt.savefig("./statics/temp/tempDailyChatRank.jpg")
    plt.close()
    return [
        "None",
        MessageChain.create([
            Image.fromLocalFile("./statics/temp/tempDailyChatRank.jpg")
        ])
    ]
