import aiohttp

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.config import GlobalConfig
from sagiri_bot.internal_utils import get_command
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("PoisonousChickenSoup")
channel.author("SAGIRI-kawaii")
channel.description("一个获取毒鸡汤的插件，在群中发送 `[鸡汤|毒鸡汤|来碗鸡汤]` 即可")

config = create(GlobalConfig)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            FrequencyLimit.require("poisonous_chicken_soup", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def poisonous_chicken_soup(app: Ariadne, group: Group):
    url = "https://api.shadiao.app/du"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            text = (await resp.json())["data"].get("text", "未找到数据")
    await app.send_group_message(group, MessageChain(text))
