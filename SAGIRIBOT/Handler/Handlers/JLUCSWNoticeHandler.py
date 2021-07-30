import re
import aiohttp
from bs4 import BeautifulSoup

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def jlu_csw_notice_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await JLUCSWNoticeHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class JLUCSWNoticeHandler(AbstractHandler):
    __name__ = "JLUCSWNoticeHandler"
    __description__ = "一个可以获取吉林大学软件学院教务通知的Handler"
    __usage__ = "在群中发送 `教务通知` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay() == "教务通知":
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return await JLUCSWNoticeHandler.format_output_notices()
        else:
            return None

    @staticmethod
    async def get_jlu_csw_notice(top: int = 100000):
        url = "http://csw.jlu.edu.cn/index/"
        host = "http://csw.jlu.edu.cn/"
        records = list()

        # 首页爬取
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{url}jbtz.htm") as resp:
                resp.encoding = "UTF-8"
                html = await resp.read()

        soup = BeautifulSoup(html, "html.parser")
        lis = soup.find("div", {"class": "text-list"}).find("ul").find_all("li")
        for li in lis:
            record = dict()
            record["time"] = li.find("span", {"class": "time"}).get_text()[-10:]
            record["title"] = li.find("div", {"class": "title"}).find("a").get_text()
            href = li.find("div", {"class": "title"}).find("a", href=True)["href"].replace("../", host)
            record["href"] = href
            records.append(record)

        # 查询页数
        html = html.decode()
        times = re.findall("<a href=\"jbtz/(.*?).htm\" class=\"Next\">下页</a>", html, re.S)

        count = 0

        # 全部数据爬取
        if times:
            times = int(times[0])
            for i in range(times):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=f"{url}jbtz/{times - i}.htm") as resp:
                        resp.encoding = "UTF-8"
                        html = await resp.read()
                soup = BeautifulSoup(html, "html.parser")
                lis = soup.find("div", {"class": "text-list"}).find("ul").find_all("li")
                for li in lis:
                    if (count := count + 1) > top:
                        break
                    record = dict()
                    record["time"] = li.find("span", {"class": "time"}).get_text()[-10:]
                    record["title"] = li.find("div", {"class": "title"}).find("a").get_text()
                    href = li.find("div", {"class": "title"}).find("a", href=True)["href"].replace("../", host)
                    record["href"] = href
                    records.append(record)
                if count > top:
                    break

        def get_time(item):
            return item["time"]

        records.sort(key=get_time, reverse=True)
        return records

    @staticmethod
    async def format_output_notices(top: int = 10) -> MessageItem:
        data = await JLUCSWNoticeHandler.get_jlu_csw_notice(top)
        content = "----------------------------------\n"
        for i in range(10):
            content += f"{data[i]['title']}\n"
            content += f"{data[i]['href']}\n"
            content += f"                                        {data[i]['time'].replace('-', '.')}\n"
            content += "----------------------------------\n"
        return MessageItem(MessageChain.create([Plain(text=content)]), Normal(GroupStrategy()))