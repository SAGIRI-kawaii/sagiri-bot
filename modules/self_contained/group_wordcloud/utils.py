import random
import asyncio
import PIL.Image
import numpy as np
import jieba.analyse
from io import BytesIO
from pathlib import Path
from typing import Literal
from datetime import datetime
from sqlalchemy import select
from matplotlib import pyplot as plt
from dateutil.relativedelta import relativedelta
from wordcloud import WordCloud, ImageColorGenerator

from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model.relationship import Group, Member

from shared.orm import orm
from shared.utils.image import get_image
from shared.orm.tables import ChatRecord

REVIEW_TYPE = Literal["年内", "今年", "年度", "月内", "本月", "月度", "今日", "本日", "日度"]


def word_filter(words: list[str]) -> list[str]:
    not_filter = ["草"]
    filter_list = {"jpg", "png", "img-", "{", "}", "<", ">", "url", "pid", "p0", "www", ":/", "qq"}
    image_filter = "mirai:"
    result = []
    for i in words:
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


async def get_words(group: int | Group, member: int | Member | None, time_left: datetime) -> list[str]:
    res = await orm.fetchall(
        select(ChatRecord.seg)
        .where(ChatRecord.group_id == int(group))
        .where(ChatRecord.member_id == int(member) if member else True)
        .where(ChatRecord.time > time_left)
    )
    return word_filter([i[0] for i in res if i[0]])


def draw_word_cloud(read_name, mask: PIL.Image.Image) -> bytes:
    mask = np.array(mask if mask else PIL.Image.open(random.choice(list((Path.cwd() / "resources" / "wordcloud").glob("*")))))
    wc = WordCloud(
        font_path=(Path.cwd() / "resources" / "fonts" / "STKAITI.TTF").as_posix(),
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


async def get_review(
    group: int | Group, member: int | Member | None, review_type: REVIEW_TYPE, mask: Image | None, top_k: int = 1000
) -> MessageChain:
    time = datetime.now()
    time_right_str = time.strftime("%Y-%m-%d %H:%M:%S")
    if review_type in ("年内", "今年", "年度"):
        time_left = time - relativedelta(years=1)
        time_left_str = (time - relativedelta(years=1)).strftime("%Y-%m-%d %H:%M:%S")
    elif review_type in ("月内", "本月", "月度"):
        time_left = time - relativedelta(months=1)
        time_left_str = (time - relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        time_left = time - relativedelta(days=1)
        time_left_str = (time - relativedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    words = await get_words(group, member, time_left)
    if not words:
        return MessageChain("没有你的发言记录呐~")
    count = len(words)
    if mask:
        mask = PIL.Image.open(BytesIO(await get_image(mask.url)))
    return MessageChain([
        "记录时间：\n"
        f"{time_left_str}"
        "\n---------至---------\n"
        f"{time_right_str}"
        "\n自有记录以来，"
        f"{'你' if member else '本群'}"
        f"一共发了{count}条消息\n下面是"
        f"{'你的' if member else '本群的'}"
        f"{review_type}词云:\n",
        Image(
            data_bytes=await asyncio.to_thread(
                draw_word_cloud,
                jieba.analyse.extract_tags(" ".join(words), topK=top_k, withWeight=True, allowPOS=()),
                mask,
            )
        ),
    ])
