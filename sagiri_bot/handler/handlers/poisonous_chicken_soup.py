from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.parser.twilight import RegexMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("PoisonousChickenSoup")
channel.author("SAGIRI-kawaii")
channel.description("一个获取毒鸡汤的插件，在群中发送 `[鸡汤|毒鸡汤|来碗鸡汤]` 即可")

core = AppCore.get_core_instance()
config = core.get_config()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"(鸡汤|毒鸡汤|来碗鸡汤)$")])],
        decorators=[
            FrequencyLimit.require("poisonous_chicken_soup", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def poisonous_chicken_soup(app: Ariadne, group: Group):
    url = f"https://api.shadiao.app/du"
    async with get_running(Adapter).session.get(url=url) as resp:
        text = (await resp.json())["data"].get("text", "未找到数据")
    await app.sendGroupMessage(group, MessageChain(text))
