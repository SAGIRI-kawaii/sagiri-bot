import time
import random
import aiohttp
import asyncio
from loguru import logger

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.scheduler.timers import crontabify
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.element import Plain, Image
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from sagiri_bot.utils import group_setting
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.core.app_core import AppCore

saya = Saya.current()
channel = Channel.current()
host_qq = AppCore.get_core_instance().get_config().host_qq


@channel.use(SchedulerSchema(crontabify("30 8 * * *")))
async def something_scheduled(app: Ariadne):
    await send_newspaper(app)


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("发送早报")})],
    )
)
async def main(app: Ariadne, friend: Friend):
    if not friend.id == host_qq:
        return None
    await send_newspaper(app)


async def send_newspaper(app: Ariadne):
    for i in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://api.2xb.cn/zaob") as resp:
                    image_url = (await resp.json()).get("imageUrl", None)
                async with session.get(image_url) as resp:
                    image_content = await resp.read()
            break
        except Exception as e:
            logger.error(f"第 {i + 1} 次日报加载失败\n{e}")
            await asyncio.sleep(3)
    for group in await app.getGroupList():
        if not await group_setting.get_setting(group, Setting.daily_newspaper):
            continue
        await app.sendMessage(group, MessageChain.create(Image(data_bytes=image_content)))
        await asyncio.sleep(random.randint(3, 6))
