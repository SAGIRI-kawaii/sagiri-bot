import aiohttp

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender

saya = Saya.current()
channel = Channel.current()

channel.name("GithubInfo")
channel.author("SAGIRI-kawaii")
channel.description("可以搜索Github项目信息的插件，在群中发送 `github [-i] {项目名}`")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def github_info(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await GithubInfo.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class GithubInfo(AbstractHandler):
    __name__ = "GithubInfo"
    __description__ = "可以搜索Github项目信息的插件"
    __usage__ = "在群中发送 `github [-i] {项目名}`"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
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
                return MessageItem(MessageChain.create([Plain(text="没有搜索到结果呢~")]), QuoteSource())
            if image:
                img_url += result[0]["full_name"]
                return MessageItem(MessageChain.create([Image(url=img_url)]), QuoteSource())
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
                    QuoteSource()
                )