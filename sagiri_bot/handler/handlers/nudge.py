import asyncio
import re
from datetime import datetime

from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne, Friend
from dateutil.relativedelta import relativedelta
from graia.ariadne.event.mirai import NudgeEvent
from graia.ariadne.message.element import Plain, At
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.strategy import Normal
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()
core: AppCore = AppCore.get_core_instance()
config = core.get_config()

channel.name("Nudge")
channel.author("nullqwertyuiop")
channel.description("1. 被戳时自动触发\n"
                    "2. `戳我[n次]`\n"
                    "3. `戳{@目标}[n次]")


@channel.use(ListenerSchema(listening_events=[NudgeEvent]))
async def nudged(app: Ariadne, event: NudgeEvent):
    if event.target == config.bot_qq:
        if event.context_type == "group":
            await Nudge.nudged(app, event)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def nudge(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await Nudge.handle(app, message, group=group, member=member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class Nudge(AbstractHandler):
    __name__ = "Nudge"
    __description__ = "戳一戳 Handler"
    __usage__ = "None"
    nudge_data = {}
    nudged_data = {}
    refresh_time = relativedelta(minutes=1)

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group = None,
                     member: Member = None, friend: Friend = None):
        if message.asDisplay().startswith("戳"):
            if message.asDisplay()[1] == "我":
                target = member
            elif message.has(At):
                target = await app.getMember(group, message.get(At)[0].target)
                if not target:
                    return None
            else:
                return None
            plain_msg = "".join(i.text.strip() for i in message.get(Plain))
            exp = r"戳我? *(\d+) *次?"
            if times := re.compile(exp).search(plain_msg):
                times = int(times.group(1))
            else:
                times = 1
            if times > 10:
                return MessageItem(MessageChain.create([Plain(text="太多次啦！")]), Normal())
            count = 0
            if target.group.id not in Nudge.nudge_data.keys():
                Nudge.nudge_data[target.group.id] = {member.id: {"count": 0, "time": datetime.now()}}
            elif member.id not in Nudge.nudge_data[target.group.id].keys():
                Nudge.nudge_data[target.group.id][member.id] = {"count": 0, "time": datetime.now()}
            else:
                period = Nudge.nudge_data[target.group.id][member.id]["time"] + Nudge.refresh_time
                if datetime.now() >= period:
                    Nudge.nudge_data[target.group.id][member.id] = {"count": 0, "time": datetime.now()}
                count = Nudge.nudge_data[target.group.id][member.id]['count']
            if count >= 10 or count + times > 10:
                return MessageItem(MessageChain.create([Plain(text="有完没完？")]), Normal())
            for i in range(times):
                try:
                    await app.sendNudge(target)
                    count += 1
                    await asyncio.sleep(0.25)
                except:
                    return MessageItem(MessageChain.create([Plain(text="戳不了啦！")]), Normal())
            Nudge.nudge_data[target.group.id][member.id]['count'] = count
            Nudge.nudge_data[target.group.id][member.id]['time'] = datetime.now()

    @staticmethod
    async def nudged(app: Ariadne, event: NudgeEvent):
        if member := await app.getMember(event.group_id, event.supplicant):
            logger.info(f"机器人被群 <{member.group.name}> 中用户 <{member.name}> 戳了戳。")
            if member.group.id in Nudge.nudged_data.keys():
                if member.id in Nudge.nudged_data[member.group.id].keys():
                    period = Nudge.nudged_data[member.group.id][member.id]["time"] + Nudge.refresh_time
                    if datetime.now() >= period:
                        Nudge.nudged_data[member.group.id][member.id] = {"count": 0, "time": datetime.now()}
                    count = Nudge.nudged_data[member.group.id][member.id]["count"] + 1
                    if count == 1:
                        try:
                            await app.sendNudge(member)
                        except:
                            pass
                        Nudge.nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                    elif count == 2:
                        try:
                            await app.sendNudge(member)
                            await app.sendMessage(
                                member.group, MessageChain.create([
                                    Plain(text=f"不许戳了！")
                                ])
                            )
                        except:
                            pass
                        Nudge.nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                    elif count == 3:
                        try:
                            await app.sendNudge(member)
                            await app.sendMessage(
                                member.group, MessageChain.create([
                                    Plain(text=f"说了不许再戳了！")
                                ])
                            )
                        except:
                            pass
                        Nudge.nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                    elif count == 4:
                        try:
                            await app.sendNudge(member)
                        except:
                            pass
                        Nudge.nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                    elif count == 5:
                        try:
                            await app.sendNudge(member)
                            await app.sendMessage(
                                member.group, MessageChain.create([
                                    Plain(text=f"呜呜呜你欺负我，不理你了！")
                                ])
                            )
                        except:
                            pass
                        Nudge.nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                    elif 6 <= count <= 9:
                        Nudge.nudged_data[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                    elif count == 10:
                        try:
                            await app.sendNudge(member)
                            await app.sendMessage(
                                member.group, MessageChain.create([
                                    Plain(text="你真的很有耐心欸。")
                                ])
                            )
                        except:
                            pass
                else:
                    Nudge.nudged_data[member.group.id][member.id] = {"count": 1, "time": datetime.now()}
                    await app.sendNudge(member)
            else:
                Nudge.nudged_data[member.group.id] = {member.id: {"count": 1, "time": datetime.now()}}
                await app.sendNudge(member)
