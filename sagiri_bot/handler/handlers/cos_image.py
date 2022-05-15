import asyncio
from datetime import datetime, timedelta

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, ForwardNode, Forward
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("CosImage")
channel.author("hcxx, nullqwertyuiop")
channel.description("获取接口cos图片，https://ovooa.com/API/cosplay/api.php，发送`cos图`即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("cos图"), RegexMatch(r"-\d+", optional=True) @ "nums"])
        ],
        decorators=[
            FrequencyLimit.require("cos_image", 2),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def cos_image(app: Ariadne, group: Group, nums: RegexResult):
    if nums.matched:
        nums = int(nums.result.asDisplay()[1:])
    else:
        nums = 1
    await send_cos_image(app, group, nums)


async def send_cos_image(app: Ariadne, group: Group, nums: int):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://ovooa.com/API/cosplay/api.php") as resp:
                image_url_arr = (await resp.json()).get("data", None).get("data", None)
            image_num = min(len(image_url_arr), nums)
            if image_num == 1:
                async with session.get(image_url_arr[0]) as resp:
                    image_content = await resp.read()
                return await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=image_content)))
            fwd_nodes = []
            for i in range(image_num):
                fwd_nodes.append(
                    ForwardNode(
                        target=app.account,
                        name="Bot",
                        time=datetime.now() + timedelta(seconds=15 * i),
                        message=MessageChain.create(Image(url=image_url_arr[i])),
                    )
                )
            await app.sendMessage(group, MessageChain.create(Forward(nodeList=fwd_nodes)))
    except Exception as e:
        logger.error({e})
        await app.sendGroupMessage(group, MessageChain("cos图获取失败，请告知我主人哦"))
        await asyncio.sleep(3)
