import aiohttp

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await GithubInfoHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class GithubInfoHandler(AbstractHandler):
    __name__ = "GithubInfoHandler"
    __description__ = "可以搜索Github信息的Handler"
    __usage__ = "None"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("github "):
            image: bool = False
            keyword = message.asDisplay()[7:]
            url = "https://api.github.com/search/repositories?q="
            img_url = "https://opengraph.githubassets.com/c9f4179f4d560950b2355c82aa2b7750bffd945744f9b8ea3f93cc24779745a0/"
            if message.asDisplay().startswith("github -i "):
                keyword = keyword[3:]
                image = True
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url + keyword) as resp:
                    result = (await resp.json())["items"]
            if not result:
                return MessageItem(MessageChain.create([Plain(text="没有搜索到结果呢~")]), QuoteSource(GroupStrategy()))
            if image:
                img_url += result[0]["full_name"]
                return MessageItem(MessageChain.create([Image.fromNetworkAddress(img_url)]), QuoteSource(GroupStrategy()))
            else:
                result = result[0]
                name = result["name"]
                owner = result["owner"]["login"]
                description = result["description"]
                repo_url = result["html_url"]
                stars = result["stargazers_count"]
                watchers = result["watchers"]
                language = result["language"]
                forks = result["forks"]
                issues = result["open_issues"]
                license = result["license"]["key"] if result["license"] else "无"
                return MessageItem(
                    MessageChain.create([
                        Plain(text=f"名称：{name}\n"),
                        Plain(text=f"作者：{owner}\n"),
                        Plain(text=f"描述：{description}\n"),
                        Plain(text=f"链接：{repo_url}\n"),
                        Plain(text=f"stars：{stars}\n"),
                        Plain(text=f"watchers：{watchers}\n"),
                        Plain(text=f"forks：{forks}\n"),
                        Plain(text=f"issues：{issues}\n"),
                        Plain(text=f"language：{language}\n"),
                        Plain(text=f"license：{license}")
                    ]),
                    QuoteSource(GroupStrategy())
                )