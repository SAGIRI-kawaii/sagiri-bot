import re
import random
import asyncio
from loguru import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.event.mirai import NudgeEvent
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, Member
from graia.ariadne.message.parser.twilight import MatchResult
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.config import GlobalConfig
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.internal_utils import group_setting

saya = Saya.current()
channel = Channel.current()
config = create(GlobalConfig)

channel.name("Nudge")
channel.author("nullqwertyuiop")
channel.description("1. 被戳时自动触发\n"
                    "2. `戳我[n次]`\n"
                    "3. `戳{@目标}[n次]")

nudge_data = {}
nudged_data = {}
refresh_time = relativedelta(minutes=1)


@channel.use(ListenerSchema(listening_events=[NudgeEvent]))
async def nudged(app: Ariadne, event: NudgeEvent):
    if not await group_setting.get_setting(event.group_id, Setting.switch):
        return None
    if event.target == config.bot_qq and event.supplicant != config.bot_qq:
        if event.context_type == "group":
            if member := await app.get_member(event.group_id, event.supplicant):
                logger.info(f"机器人被群 <{member.group.name}> 中用户 <{member.name}> 戳了戳。")
                if member.group.id in nudged_data.keys():
                    if member.id in nudged_data[member.group.id].keys():
                        period = nudged_data[member.group.id][member.id]["time"] + refresh_time
                        if datetime.now() >= period:
                            nudged_data[member.group.id][member.id] = {"count": 0, "time": datetime.now()}
                        count = nudged_data[member.group.id][member.id]["count"] + 1
                        if count == 1:
                            try:
                                await app.send_nudge(member)
                            except UnknownTarget:
                                pass
                            nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 2:
                            try:
                                await app.send_nudge(member)
                                await app.send_message(
                                    member.group, MessageChain([
                                        Plain(text=f"不许戳了！")
                                    ])
                                )
                            except UnknownTarget:
                                pass
                            nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 3:
                            try:
                                await app.send_nudge(member)
                                await app.send_message(
                                    member.group, MessageChain([
                                        Plain(text=f"说了不许再戳了！")
                                    ])
                                )
                            except UnknownTarget:
                                pass
                            nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 4:
                            try:
                                await app.send_nudge(member)
                            except UnknownTarget:
                                pass
                            nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 5:
                            try:
                                await app.send_nudge(member)
                                await app.send_message(
                                    member.group, MessageChain([
                                        Plain(text=f"呜呜呜你欺负我，不理你了！")
                                    ])
                                )
                            except UnknownTarget:
                                pass
                            nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif 6 <= count <= 9:
                            nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 10:
                            try:
                                await app.send_nudge(member)
                                await app.send_message(
                                    member.group, MessageChain([
                                        Plain(text="你真的很有耐心欸。")
                                    ])
                                )
                            except UnknownTarget:
                                pass
                    else:
                        nudged_data[member.group.id][member.id] = {"count": 1, "time": datetime.now()}
                        await app.send_nudge(member)
                else:
                    nudged_data[member.group.id] = {member.id: {"count": 1, "time": datetime.now()}}
                    await app.send_nudge(member)


async def nudge(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    me: MatchResult,
    at: MatchResult,
    times: MatchResult
):
    if message.display == "戳":
        return None
    if me.matched and at.matched:
        return await app.send_group_message(group, MessageChain("到底戳谁？"))
    elif not me.matched and not at.matched:
        return await app.send_group_message(group, MessageChain("也不说要戳谁......"))
    if times.matched:
        times = int(re.search(r"\d+", times.result.display).group(0))
        if times > 10:
            return await app.send_group_message(group, MessageChain("太多次啦！"))
    else:
        times = 1
    target = member if me.matched else await app.get_member(group, at.result.target)
    if target:
        count = 0
        if target.group.id not in nudge_data.keys():
            nudge_data[target.group.id] = {member.id: {"count": 0, "time": datetime.now()}}
        elif member.id not in nudge_data[target.group.id].keys():
            nudge_data[target.group.id][member.id] = {"count": 0, "time": datetime.now()}
        else:
            period = nudge_data[target.group.id][member.id]["time"] + refresh_time
            if datetime.now() >= period:
                nudge_data[target.group.id][member.id] = {"count": 0, "time": datetime.now()}
            count = nudge_data[target.group.id][member.id]['count']
        if count >= 10 or count + times > 10:
            return await app.send_group_message(group, MessageChain("有完没完？"))
        for _ in range(times):
            await app.send_nudge(target)
            count += 1
            await asyncio.sleep(0.25 * random.randint(1, 5))
        nudge_data[target.group.id][member.id]['count'] = count
        nudge_data[target.group.id][member.id]['time'] = datetime.now()
