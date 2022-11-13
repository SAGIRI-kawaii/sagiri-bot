import random
import aiohttp
import asyncio
from loguru import logger

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend, Group
from graia.scheduler.timers import crontabify
from graia.ariadne.message.element import Image
from graia.ariadne.exception import AccountMuted
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import FriendMessage, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from shared.orm import Setting
from shared.models.config import GlobalConfig
from shared.utils.module_related import get_command
from shared.models.group_setting import GroupSetting
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)


saya = Saya.current()
channel = Channel.current()
host_qq = create(GlobalConfig).host_qq

channel.name("DailyNewspaper")
channel.author("SAGIRI-kawaii")
channel.description("一个定时发送每日日报的插件\n主人私聊bot发送 `发送早报` 可在群中发送早报\n在群中发送 `今日早报` 可在群中发送早报")

group_setting = create(GroupSetting)


@channel.use(SchedulerSchema(crontabify("30 8 * * *")))
async def something_scheduled(app: Ariadne):
    await send_newspaper(app)


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("发送早报")])],
    )
)
async def main(app: Ariadne, friend: Friend):
    if friend.id != host_qq:
        return None
    await send_newspaper(app)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("daily_newspaper", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def send(app: Ariadne, group: Group):
    await app.send_message(group, MessageChain([Image(data_bytes=await get_image())]))


async def send_newspaper(app: Ariadne):
    image_content = None
    for i in range(3):
        try:
            image_content = await get_image()
            break
        except Exception as e:
            logger.error(f"第 {i + 1} 次日报加载失败\n{e}")
            await asyncio.sleep(3)
    if not image_content:
        return logger.error("日报获取失败！")
    for group in await app.get_group_list():
        if not await group_setting.get_setting(group, Setting.daily_newspaper):
            continue
        try:
            await app.send_message(group, MessageChain(Image(data_bytes=image_content)))
        except AccountMuted:
            continue
        await asyncio.sleep(random.randint(3, 6))


async def get_image() -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://api.2xb.cn/zaob") as resp:
            image_url = (await resp.json()).get("imageUrl", None)
        async with session.get(image_url) as resp:
            image_content = await resp.read()
    return image_content
