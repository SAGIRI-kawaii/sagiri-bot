import json
import asyncio
from pathlib import Path
from json import JSONDecodeError
from datetime import datetime, timedelta

import aiohttp
from loguru import logger
from aiohttp import BasicAuth
from graia.scheduler import timers
from graia.saya import Saya, Channel
from graia.ariadne.model import MemberPerm
from graia.ariadne.app import Ariadne, Friend
from graia.ariadne.message.element import Plain
from graia.scheduler.saya import SchedulerSchema
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.exception import UnknownTarget, AccountMuted
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, FriendMessage, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, UnionMatch, WildcardMatch

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import QuoteSource, Normal
from sagiri_bot.utils import user_permission_require, MessageChainUtils

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
core: AppCore = AppCore.get_core_instance()
app = core.get_app()
loop = core.get_loop()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ''

channel.name("GithubWatcher")
channel.author("nullqwertyuiop")
channel.description(
    "/github-watch enable [3级权限]\n"
    "/github-watch disable [3级权限]\n"
    "/github-watch add {repo} [repo]+ [2级或管理员权限]\n"
    "/github-watch remove {repo} [repo]+ [2级或管理员权限]\n"
    "/github-watch check [任何人]\n"
    "/github-watch cache {update/store} [2级或管理员权限]\n"
)


class GithubWatcher(object):
    __name__ = "GithubWatcher"
    __description__ = "Github 订阅 Handler"
    __usage__ = "None"
    __cached = {}
    if config.functions['github']['username'] != "username" and config.functions['github']['token'] != 'token':
        __auth = True
        __session = aiohttp.ClientSession(auth=BasicAuth(
            login=config.functions['github']['username'],
            password=config.functions['github']['token']
        ))
    else:
        __auth = False
        __session = aiohttp.ClientSession()
    __first_warned = False

    __status = True
    __base_url = "https://api.github.com"
    __events_url = "/repos/{owner}/{repo}/events"
    __is_running = False
    initialize = False

    @switch()
    @blacklist()
    async def real_handle(self, app: Ariadne, message: MessageChain, group: Group = None,
                          member: Member = None, friend: Friend = None) -> MessageItem:
        commands = {
            "enable": {
                "permission": [3, []],
                "permission_nl": "3 级权限",
                "manual": "/github-watch enable",
                "description": "启用 Github 订阅功能",
                "func": self.enable
            },
            "disable": {
                "permission": [3, []],
                "permission_nl": "3 级权限",
                "manual": "/github-watch disable",
                "description": "禁用 Github 订阅功能",
                "func": self.disable
            },
            "add": {
                "permission": [2, (MemberPerm.Administrator, MemberPerm.Owner)],
                "permission_nl": "2 级或群管理员及以上权限",
                "manual": "/github-watch add {repo} [repo]+",
                "description": "订阅仓库变动，可同时订阅多个仓库",
                "func": self.add
            },
            "remove": {
                "permission": [2, (MemberPerm.Administrator, MemberPerm.Owner)],
                "permission_nl": "2 级或群管理员及以上权限",
                "manual": "/github-watch remove {repo} [repo]+",
                "description": "取消订阅仓库变动，可同时取消订阅多个仓库",
                "func": self.remove
            },
            "check": {
                "permission": [1, (MemberPerm.Member, MemberPerm.Administrator, MemberPerm.Owner)],
                "permission_nl": "任何人",
                "manual": "/github-watch check",
                "description": "手动查看仓库订阅列表",
                "func": self.check
            },
            "cache": {
                "permission": [2, (MemberPerm.Administrator, MemberPerm.Owner)],
                "permission_nl": "2 级或群管理员及以上权限",
                "manual": "/github-watch cache {update/store}",
                "description": "更新/储存缓存",
                "func": self.cache
            }
        }
        if message.asDisplay().startswith("/github-watch"):
            if not self.initialize:
                self.update_cache()
                for repo in self.__cached.keys():
                    self.__cached[repo]['enabled'] = True
                self.store_cache()
                self.initialize = True
            args = message.asDisplay().split(" ", maxsplit=1)
            if len(args) == 1:
                msg = [Plain(text="缺少参数\n\n")]
                for func in commands:
                    msg.append(Plain(text=(f"/github-watch {func}\n"
                                           f"    描述：{commands[func]['description']}\n"
                                           f"    用法：{commands[func]['manual']}\n"
                                           f"    权限：{commands[func]['permission_nl']}\n")))
                return MessageItem(
                    await MessageChainUtils.messagechain_to_img(
                        MessageChain.create(msg)
                    ), QuoteSource())
            _, args = args
            name = args.split(" ", maxsplit=1)[0]
            arg = ''.join(args.split(" ", maxsplit=1)[1:])
            if name not in commands.keys():
                return MessageItem(MessageChain.create([Plain(text=f"未知指令：{arg}")]), QuoteSource())
            if member and group:
                permission = commands[name]['permission']
                if (
                    not await user_permission_require(group, member, permission[0])
                    and member.permission not in permission[1]
                ):
                    return MessageItem(MessageChain.create([Plain(
                        text=f"权限不足，你需要 {permission[0]} 级权限"
                             f"{('或来自 ' + str(permission[1][0]) + ' 的权限') if permission[1] else ''}")]), QuoteSource())
            arg = arg.strip()
            return MessageItem(await commands[name]['func'](
                app=app, group=group, friend=friend, arg=arg
            ), QuoteSource())

    async def enable(self, **kwargs):
        self.__status = True
        return MessageChain.create([Plain(text="已开启 Github 仓库订阅")])

    async def disable(self, **kwargs):
        self.__status = False
        return MessageChain.create([Plain(text="已关闭 Github 仓库订阅")])

    async def add(self, **kwargs):
        if not self.__status:
            return MessageChain.create([Plain(text="Github 仓库订阅功能已关闭")])
        repos = None
        group = None
        friend = None
        app = None
        for name, arg in kwargs.items():
            if name == "arg" and isinstance(arg, str):
                repos = arg
            if isinstance(arg, Group):
                group = arg
            if isinstance(arg, Friend):
                friend = arg
            if isinstance(arg, Ariadne):
                app = arg
        err = []
        if not group and not friend:
            err = err.extend([
                Plain(text="无法获取 Group 或 Friend 实例")
            ])
        if not app:
            err = err.extend([
                Plain(text="无法获取 Ariadne 实例")
            ])
        if not repos:
            err = err.extend([
                Plain(text="未填写需要订阅的仓库")
            ])
        if err:
            return MessageChain.create(err)
        repos = repos.split(" ")
        failed = []
        duplicated = []
        success_count = 0
        for repo in repos:
            url = f"https://api.github.com/search/repositories?q={repo}"
            async with self.__session.get(url=url, proxy=proxy) as resp:
                try:
                    resp.raise_for_status()
                except aiohttp.ClientError as e:
                    logger.error(e)
                    logger.error(f"暂时无法取得仓库 {repo} 的更新（状态码 {resp.status}）")
                    continue
                result = (await resp.json())["items"]
                if not result:
                    failed.append(repo)
                    continue
                repo = result[0]['full_name']
            repo = repo.split("/")
            repo = (repo[0], repo[1])
            if repo not in self.__cached.keys():
                self.__cached[repo] = {
                    "group": [],
                    "friend": [],
                    "last_id": -1,
                    "enabled": True
                }
            if group:
                if group.id in self.__cached[repo]['group']:
                    duplicated.append(f"{repo[0]}/{repo[1]}")
                else:
                    self.__cached[repo]['group'] = self.__cached[repo]['group'] + [group.id]
            if friend:
                if friend.id in self.__cached[repo]['friend']:
                    duplicated.append(f"{repo[0]}/{repo[1]}")
                else:
                    self.__cached[repo]['friend'] = self.__cached[repo]['friend'] + [friend.id]
            if self.__cached[repo]['last_id'] == -1:
                await self.github_schedule(app=app, manuel=True, per_page=1, page=1, repo=repo)
            success_count += 1
        res = [Plain(text=f"{success_count} 个仓库订阅成功")]
        if failed:
            res.append(Plain(text=f"\n{len(failed)} 个仓库订阅失败"
                                  f"\n失败的仓库有：{' '.join(failed)}"))
        if duplicated:
            res.append(Plain(text=f"\n{len(duplicated)} 个仓库已在订阅列表中"
                                  f"\n重复的仓库有：{' '.join(duplicated)}"))
        try:
            self.store_cache(manual=False)
            self.update_cache(manual=False)
            return MessageChain.create(res)
        except Exception as e:
            logger.error(e)
            res.append(Plain(text="\n\n刷新缓存失败"))
            return MessageChain.create(res)

    async def remove(self, **kwargs):
        if not self.__status:
            return MessageChain.create([Plain(text=f"Github 仓库订阅功能已关闭")])
        repos = None
        group = None
        friend = None
        err = []
        for name, arg in kwargs.items():
            if name == "arg" and isinstance(arg, str):
                repos = arg
            if isinstance(arg, Group):
                group = arg
            if isinstance(arg, Friend):
                friend = arg
        if not group and not friend:
            err = err.extend([
                Plain(text=f"无法获取 Group 或 Friend 实例")
            ])
        if not repos:
            err = err.extend([
                Plain(text="未填写需要取消订阅的仓库")
            ])
        if err:
            return MessageChain.create(err)
        repos = repos.split(" ")
        failed = []
        success_count = 0
        for repo in repos:
            repo = repo.split("/")
            if len(repo) != 2:
                failed.append("/".join(repo))
                continue
            repo = (repo[0], repo[1])
            if repo not in self.__cached.keys():
                failed.append("/".join(repo))
                continue
            if group:
                self.__cached[repo]['group'] = [
                    group_id for group_id in self.__cached[repo]['group'] if group_id != group.id
                ]
            if friend:
                self.__cached[repo]['friend'] = [
                    friend_id for friend_id in self.__cached[repo]['group'] if friend_id != friend.id
                ]
            if not (self.__cached[repo]['group'] and self.__cached[repo]['friend']):
                self.__cached.pop(repo)
            success_count += 1
        res = [Plain(text=f"{success_count} 个仓库取消订阅成功")]
        if failed:
            res.append(Plain(text=f"\n{len(failed)} 个仓库取消订阅失败"
                                  f"\n失败的仓库有：{' '.join(failed)}"))
        try:
            self.store_cache(manual=False)
            self.update_cache(manual=False)
            return MessageChain.create(res)
        except Exception as e:
            logger.error(e)
            res.append(Plain(text="\n\n刷新缓存失败"))
            return MessageChain.create(res)

    async def cache(self, **kwargs):
        accepted = ['update', 'store']
        command = None
        for name, arg in kwargs.items():
            if name == "arg" and isinstance(arg, str):
                command = arg
        if not command:
            return MessageChain.create([Plain(text=f"未填写参数")])
        if command not in accepted:
            return MessageChain.create([Plain(text=f"未知参数：{command}")])
        if command == 'update':
            return self.update_cache(manual=True)
        if command == 'store':
            return self.store_cache(manual=True)

    def update_cache(self, manual: bool = False):
        try:
            with open(str(Path(__file__).parent.joinpath("watcher_data.json")), "r") as r:
                data = json.loads(r.read())
                cache = {}
                for key in data.keys():
                    owner, repo = key.split("/")
                    cache[(owner, repo)] = data[key]
                self.__cached = cache
            return MessageChain.create([Plain(text="更新缓存成功")]) if manual else None
        except (FileNotFoundError, JSONDecodeError):
            return MessageChain.create([Plain(text="无法更新缓存，请检查是否删除了缓存文件并重新储存缓存")])

    def store_cache(self, manual: bool = False):
        with open(str(Path(__file__).parent.joinpath("watcher_data.json")), "w") as w:
            cache = {}
            for key in self.__cached.keys():
                new_key = f"{key[0]}/{key[1]}"
                cache[new_key] = self.__cached[key]
            w.write(json.dumps(cache, indent=4))
        return MessageChain.create([Plain(text="写入缓存成功")]) if manual else None

    async def check(self, **kwargs) -> MessageChain:
        group = None
        friend = None
        for name, arg in kwargs.items():
            if isinstance(arg, Group):
                group = arg
            if isinstance(arg, Friend):
                friend = arg
        if not group and not friend:
            return MessageChain.create([
                Plain(text=f"无法获取 Group 或 Friend 实例")
            ])
        target = group or friend
        field = 'group' if group else 'friend'
        watched = [
            f"{repo[0]}/{repo[1]}"
            for repo in self.__cached.keys()
            if target.id in self.__cached[repo][field]
        ]

        res = [Plain(text=f"{'本群' if group else '你'}订阅的仓库有：\n"
                          f"{' '.join(watched)}")]
        return MessageChain.create(res)

    async def get_repo_event(self, repo: tuple, per_page: int = 30, page: int = 1):
        url = self.__base_url \
              + self.__events_url.replace('{owner}', repo[0]).replace('{repo}', repo[1]) \
              + f'?per_page={per_page}&page={page}'
        res = None
        try:
            res = await self.__session.get(url=url, proxy=proxy)
            res.raise_for_status()
            res = await res.json()
            if isinstance(res, list):
                return res
            elif isinstance(res, dict):
                if "message" in res.keys():
                    if "API rate limit exceeded" in res["message"]:
                        logger.error("GitHub API 超出速率限制")
                        if not self.__auth:
                            logger.error("请设置 GitHub 用户名和 OAuth Token 以提高限制")
                            self.__first_warned = True
                    elif res["message"] == "Not Found":
                        logger.error(f"无法找到仓库 {repo[0]}/{repo[1]}")
                        self.__cached[repo]['enabled'] = False
            return res
        except aiohttp.ClientError as e:
            logger.error(e)
            logger.error(f"暂时无法取得仓库 {repo[0]}/{repo[1]} 的更新"
                         f"{'' if not res else '（状态码 ' + str(res.status) + '）'}")
            return None
        except Exception as e:
            logger.error(e)
            return None

    async def a_generate_plain(self, event: dict):
        return await asyncio.get_event_loop().run_in_executor(None, self.generate_plain, event)

    @staticmethod
    def generate_plain(event: dict):
        actor = event['actor']['display_login']
        event_time = (datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)) \
            .strftime('%Y-%m-%d %H:%M:%S')
        resp = None
        if event['type'] == 'IssuesEvent':
            if event['payload']['action'] == 'opened':
                title = event['payload']['issue']['title']
                number = event['payload']['issue']['number']
                body = event['payload']['issue']['body']
                if body:
                    if len(body) > 100:
                        body = body[:100] + "......"
                    body = body + "\n"
                link = event['payload']['issue']['html_url']
                resp = Plain(text=f"----------\n"
                                  f"[新 Issue]\n"
                                  f"#{number} {title}\n"
                                  f"{body}\n"
                                  f"\n"
                                  f"发布人：{actor}\n"
                                  f"时间：{event_time}\n"
                                  f"链接：{link}\n")
        elif event['type'] == 'IssueCommentEvent':
            if event['payload']['action'] == 'created':
                title = event['payload']['issue']['title']
                number = event['payload']['issue']['number']
                body = event['payload']['comment']['body']
                if body:
                    if len(body) > 100:
                        body = body[:100] + "......"
                    body = body + "\n"
                link = event['payload']['comment']['html_url']
                resp = Plain(text=f"----------\n"
                                  f"[新 Comment]\n"
                                  f"#{number} {title}\n"
                                  f"{body}"
                                  f"\n"
                                  f"发布人：{actor}\n"
                                  f"时间：{event_time}\n"
                                  f"链接：{link}\n")
        elif event['type'] == 'PullRequestEvent':
            if event['payload']['action'] == 'opened':
                title = event['payload']['pull_request']['title']
                number = event['payload']['pull_request']['number']
                body = event['payload']['pull_request']['body']
                if body:
                    if len(body) > 100:
                        body = body[:100] + "......"
                    body = body + "\n"
                head = event['payload']['pull_request']['head']['label']
                base = event['payload']['pull_request']['base']['label']
                commits = event['payload']['pull_request']['commits']
                link = event['payload']['pull_request']['html_url']
                resp = Plain(text=f"----------\n"
                                  f"[新 PR]\n"
                                  f"#{number} {title}\n"
                                  f"{body}"
                                  f"\n"
                                  f"{head} → {base}\n"
                                  f"提交数：{commits}\n"
                                  f"发布人：{actor}\n"
                                  f"时间：{event_time}\n"
                                  f"链接：{link}\n")
        elif event['type'] == 'PushEvent':
            commits = [
                f"· [{commit['author']['name']}] {commit['message']}"
                for commit in event['payload']['commits']
            ]

            resp = Plain(text=f"----------\n"
                              f"[新 Push]\n"
                              + "\n".join(commits) +
                              f"\n"
                              f"提交数：{len(commits)}\n"
                              f"发布人：{actor}\n"
                              f"时间：{event_time}\n")
        elif event['type'] == 'CommitCommentEvent':
            body = event['payload']['comment']['body']
            if body:
                if len(body) > 100:
                    body = body[:100] + "......"
                body = body + "\n"
            link = event['payload']['comment']['html_url']
            resp = Plain(text=f"----------\n"
                              f"[新 Comment]\n"
                              f"{body}"
                              f"\n"
                              f"发布人：{actor}\n"
                              f"时间：{event_time}\n"
                              f"链接：{link}\n")
        return resp or None

    async def github_schedule(self, **kwargs):
        if not self.initialize:
            self.update_cache()
            self.initialize = True
        try:
            app = None
            manual = False
            repo = None
            per_page = 30
            page = 1
            for name, arg in kwargs.items():
                if name == "manual" and isinstance(arg, bool):
                    manual = arg
                if name == "repo" and isinstance(arg, tuple):
                    repo = arg
                if name == "per_page" and isinstance(arg, int):
                    per_page = arg
                if name == "page" and isinstance(arg, int):
                    page = arg
                if isinstance(arg, Ariadne):
                    app = arg
            if not app:
                logger.error("无法获得 Ariadne 实例")
                return None
            if self.__is_running:
                if manual:
                    return MessageItem(MessageChain.create([Plain(
                        text="Github 订阅插件正在进行其他操作，请稍后再试。"
                    )]), QuoteSource())
                return None
            if self.__status and repo:
                res = []
                if events := await self.get_repo_event(repo, per_page, page):
                    if isinstance(events, list):
                        self.__cached[repo]['last_id'] = int(events[0]['id'])
                        if resp := await self.a_generate_plain(events[0]):
                            res.append(resp)
                    else:
                        res.append(Plain(text=events["message"]))
                if not res:
                    return None
                res.insert(0, Plain(text=f"仓库：{repo[0]}/{repo[1]}\n"))
                res.append(Plain(text=f"----------\n获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
                return MessageChain.create(res)
            if self.__status:
                self.__is_running = True
                for repo in self.__cached.keys():
                    if not self.__cached[repo]['enabled']:
                        continue
                    res = []
                    if events := await self.get_repo_event(repo, per_page, page):
                        if isinstance(events, list):
                            last_id = self.__cached[repo]['last_id']
                            new_last_id = last_id
                            for index, event in enumerate(events):
                                if index == 0:
                                    new_last_id = int(event['id'])
                                if int(event['id']) <= last_id:
                                    break
                                if resp := await self.a_generate_plain(event):
                                    res.append(resp)
                                else:
                                    continue
                            self.__cached[repo]['last_id'] = new_last_id
                            self.store_cache()
                        else:
                            res.append(Plain(text=events["message"]))
                    if res:
                        if res[0].asDisplay() == "Bad credentials":
                            self.__is_running = False
                            self.__status = False
                            await app.sendFriendMessage(
                                config.host_qq, MessageChain.create([
                                    Plain(text="凭据无效，请检查是否已更改或吊销 Github Token\n"
                                               "已自动关闭 Github Watcher")
                                ])
                            )
                            raise Exception("凭据无效，请检查是否已更改或吊销 Github Token")
                        res.insert(0, Plain(text=f"仓库：{repo[0]}/{repo[1]}\n"))
                        res.append(Plain(text=f"----------\n获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
                        res = MessageChain.create(res)
                        # fwd_nodes = [
                        #     ForwardNode(
                        #         senderId=config.bot_qq,
                        #         time=datetime.now(),
                        #         senderName="Github 订阅",
                        #         messageChain=MessageChain.create(Plain(text=f"仓库：{repo[0]}/{repo[1]}\n")),
                        #     )
                        # ]
                        # for index, element in enumerate(res):
                        #     fwd_nodes.append(
                        #         ForwardNode(
                        #             senderId=config.bot_qq,
                        #             time=datetime.now() + timedelta(minutes=index + 1),
                        #             senderName="Github 订阅",
                        #             messageChain=MessageChain.create(element),
                        #         )
                        #     )
                        # fwd_nodes.append(
                        #     ForwardNode(
                        #         senderId=config.bot_qq,
                        #         time=datetime.now(),
                        #         senderName="Github 订阅",
                        #         messageChain=MessageChain.create(Plain(
                        #             text=f"获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        #         ),
                        #     )
                        # )
                        # res = MessageChain.create(Forward(nodeList=fwd_nodes))
                        if manual:
                            self.__is_running = False
                            return MessageItem(res, Normal())
                        for group in self.__cached[repo]['group']:
                            try:
                                await app.sendGroupMessage(group, res)
                            except (AccountMuted, UnknownTarget):
                                pass
                        for friend in self.__cached[repo]['friend']:
                            try:
                                await app.sendFriendMessage(friend, res)
                            except UnknownTarget:
                                pass
                self.__is_running = False
            else:
                if manual:
                    return MessageItem(MessageChain.create([Plain(text="Github 订阅插件已关闭。")]), QuoteSource())
        except Exception as e:
            logger.error(e)
            self.__is_running = False


gw = GithubWatcher()


@channel.use(SchedulerSchema(timer=timers.every_minute()))
async def github_schedule(app: Ariadne):
    try:
        await gw.github_schedule(app=app, manual=False)
    except:
        pass


twilight = Twilight(
    [
        FullMatch("/github-watch "),
        UnionMatch("disable", "add", "remove", "check", "cache"),
        WildcardMatch()
    ]
)


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        # inline_dispatchers=[twilight]
    )
)
async def github_watcher_friend_handler(app: Ariadne, message: MessageChain, friend: Friend):
    if result := await gw.real_handle(app, message, friend=friend):
        await MessageSender(result.strategy).send(app, result.message, message, friend, friend)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        # inline_dispatchers=[twilight]
    )
)
async def github_watcher_group_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await gw.real_handle(app, message, group=group, member=member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)
