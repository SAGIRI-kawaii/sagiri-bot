import os
import time
import numpy as np
from io import BytesIO
from scipy import interpolate
from sqlalchemy import select
import matplotlib.pyplot as plt
from sqlalchemy.sql import func
from typing import Optional, List
from datetime import datetime, timedelta
from matplotlib.font_manager import FontProperties

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, ArgumentMatch, ArgResult

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.orm.async_orm import ChatRecord
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Permission,
)

saya = Saya.current()
channel = Channel.current()

channel.name("MessageStatistic")
channel.author("SAGIRI-kawaii")
channel.description("bot管理插件，必要插件，请勿卸载！否则会导致管理功能失效（若失效请重启机器人）")

font = f"{os.getcwd()}/statics/fonts/STKAITI.TTF"
zhfont1 = FontProperties(fname=font)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("消息量统计"),
                    ArgumentMatch("-group", action="store_true", optional=True)
                    @ "group_only",
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("message_statistic", 1),
            Function.require(channel.module, notice=True, response_administrator=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
            Permission.require(Permission.GROUP_ADMIN),
        ],
    )
)
async def message_statistic(app: Ariadne, group: Group, group_only: ArgResult):
    if group_only.matched:
        return await app.send_group_message(
            group, await get_message_statistic(group=group)
        )
    else:
        return await app.send_group_message(group, await get_message_statistic())


def get_last_time(hour: int = 24) -> datetime:
    curr_time = datetime.now()
    return curr_time - timedelta(hours=hour)


async def get_message_statistic(group: Optional[Group] = None) -> MessageChain:
    last_time = get_last_time(23)
    now = time.localtime(time.time())
    hour = now.tm_hour
    expect_hours = [(hour - i) % 24 for i in range(24)]
    expect_hours = [f"{i}" if i >= 10 else f"0{i}" for i in expect_hours][::-1]
    start = time.time()
    data = await orm.fetchall(
        select(func.strftime("%H", ChatRecord.time), func.count(ChatRecord.id))
        .where(
            ChatRecord.time >= last_time,
            ChatRecord.group_id == group.id if group else True,
        )
        .group_by(func.strftime("%H", ChatRecord.time))
    )
    print(f"use {time.time() - start}s")
    data = {item[0]: item[1] for item in data}
    talk_num = []
    for i in expect_hours:
        if i in data:
            talk_num.append(data[i])
        else:
            talk_num.append(0)
    return MessageChain(
        [
            Image(
                data_bytes=get_mapping(
                    [f"{i}:00" for i in expect_hours],
                    talk_num,
                    group.name if group else "",
                )
            )
        ]
    )


def get_mapping(
    time_tags: List[str], talk_num: List[int], group_name: str = ""
) -> bytes:
    if group_name:
        group_name = f"群 <{group_name}> "
    x_range = range(1, 25)
    x = np.array(x_range)
    y = np.array(talk_num)
    x_new = np.linspace(x.min(), x.max(), 600)

    y_new = interpolate.splev(x_new, interpolate.splrep(x, y))

    plt.figure(dpi=200, figsize=(18, 7))
    plt.plot(x_new, y_new, c="violet", linewidth=3)
    plt.fill_between(x_new, y_new, 0, facecolor="violet", alpha=0.5)
    plt.scatter(x, y, c="violet", linewidths=2)
    plt.scatter(x, y, c="white", s=6).set_zorder(10)
    plt.xticks(x_range, labels=time_tags)

    for a, b in zip(x, y):
        plt.text(a, b + 5, "%.0f" % b, ha="center", va="bottom", fontsize=12)

    plt.title(
        f"{group_name}消息量统计（24h内共 {sum(talk_num)} 条）",
        fontsize=36,
        fontproperties=zhfont1,
    )
    plt.tick_params(axis="both", labelsize=12)

    bio = BytesIO()
    plt.savefig(bio)
    return bio.getvalue()
