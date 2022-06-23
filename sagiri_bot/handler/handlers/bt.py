from datetime import datetime
from bs4 import BeautifulSoup

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import ForwardNode, Forward, Source
from graia.ariadne.message.parser.twilight import FullMatch, WildcardMatch, RegexResult

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("BTSearcher")
channel.author("SAGIRI-kawaii")
channel.description("一个可以搜索bt的插件，在群中发送 `/bt + 想搜索的内容` 即可")

config = AppCore.get_core_instance().get_config()
base_url = "http://www.eclzz.win"
url = base_url + "/s/{keyword}.html"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/bt"), WildcardMatch() @ "keyword"])],
        decorators=[
            FrequencyLimit.require("bt_searcher", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def bt_searcher(app: Ariadne, message: MessageChain, group: Group, keyword: RegexResult):
    keyword = keyword.result.asDisplay().strip()
    search_url = url.format(keyword=keyword)
    async with get_running(Adapter).session.get(search_url) as resp:
        html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", {"class": "search-item"})
    if not divs:
        return await app.sendGroupMessage(
            group, MessageChain(f"没有找到有关{keyword}的结果呢~"), quote=message.getFirst(Source)
        )
    forward_list = []
    for div in divs[:5]:
        title = div.find("h3").get_text().strip()[1:]
        items = div.find("div", {"class": "item-list"}).get_text().strip().split(';')
        spans = div.find("div", {"class": "item-bar"}).find_all("span")
        file_type = spans[0].get_text().strip()
        create_time = spans[1].find("b").get_text().strip()
        file_size = spans[2].find("b").get_text().strip()
        file_trend = spans[3].find("b").get_text().strip()
        async with get_running(Adapter).session.get(base_url + div.find("a")["href"]) as resp:
            magnet = BeautifulSoup(await resp.text(), "html.parser").find("input", {"id": "m_link"})["value"]
        forward_list.append(
            ForwardNode(
                senderId=config.bot_qq,
                time=datetime.now(),
                senderName="纱雾酱",
                messageChain=MessageChain(
                    f"标题：{title}\n"
                    f"文件大小：{file_size}\n"
                    f"收录时间：{create_time}\n"
                    f"文件种类：{file_type}\n"
                    f"文件热度：{file_trend}\n"
                    f"磁力链接：{magnet}\n"
                    f"文件列表：\n    " +
                    "\n    ".join(items)
                )
            )
        )
    await app.sendGroupMessage(group, MessageChain([Forward(forward_list)]))
