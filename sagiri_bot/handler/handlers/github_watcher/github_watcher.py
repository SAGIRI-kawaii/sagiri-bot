import asyncio
import json
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget, AccountMuted
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Group, Friend
from graia.saya import Saya
from graia.scheduler import GraiaScheduler
from graia.scheduler.timers import crontabify
from loguru import logger

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.strategy import Normal, QuoteSource

saya = Saya.current()
bcc = saya.broadcast
core: AppCore = AppCore.get_core_instance()
app = core.get_app()
loop = core.get_loop()
scheduler = GraiaScheduler(loop, bcc)


class GithubWatcher:
    __name__ = "GithubWatcher"
    __description__ = "Github 订阅 Handler"
    __usage__ = "None"
    cached = {}
    '''
    cached = {
        ("owner", "repo"): {
            "group": [114514],
            "friend": [1919810],
            "last_id": 1145141919,
            "enabled": True
        }
    }
    '''
    session = aiohttp.ClientSession()
    status = True
    base_url = "https://api.github.com"
    events_url = "/repos/{owner}/{repo}/events"
    is_running = False
    initialize = False

    @staticmethod
    async def enable(**kwargs):
        GithubWatcher.status = True
        return MessageChain.create([Plain(text="已开启 Github 仓库订阅")])

    @staticmethod
    async def disable(**kwargs):
        GithubWatcher.status = False
        return MessageChain.create([Plain(text="已关闭 Github 仓库订阅")])

    @staticmethod
    async def add(**kwargs):
        """
        说明：
            添加订阅
        参数：
            :**kwarg app: Ariadne 实例
            :**kwarg arg: 仓库名，需以字符串形式传入
            :**kwarg group: Group 实例，默认为 None
            :**kwarg friend: Friend 实例，默认为 None
        """
        if not GithubWatcher.status:
            return MessageChain.create([Plain(text=f"Github 仓库订阅功能已关闭")])
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
        if not group and not friend:
            return MessageChain.create([
                Plain(text="无法获取 Group 或 Friend 实例")
            ])
        if not app:
            return MessageChain.create([
                Plain(text="无法获取 Ariadne 实例")
            ])
        if not repos:
            return MessageChain.create([
                Plain(text="未填写需要订阅的仓库")
            ])
        repos = repos.split(" ")
        failed = []
        duplicated = []
        success_count = 0
        for repo in repos:
            url = f"https://api.github.com/search/repositories?q={repo}"
            async with GithubWatcher.session.get(url=url) as resp:
                result = (await resp.json())["items"]
                repo = result[0]['full_name']
            if not result:
                failed.append(repo)
                continue
            repo = repo.split("/")
            repo = (repo[0], repo[1])
            if repo not in GithubWatcher.cached.keys():
                GithubWatcher.cached[repo] = {
                    "group": [],
                    "friend": [],
                    "last_id": -1,
                    "enabled": True
                }
            if group:
                if group.id in GithubWatcher.cached[repo]['group']:
                    duplicated.append(f"{repo[0]}/{repo[1]}")
                else:
                    GithubWatcher.cached[repo]['group'] = GithubWatcher.cached[repo]['group'] + [group.id]
            if friend:
                if friend.id in GithubWatcher.cached[repo]['friend']:
                    duplicated.append(f"{repo[0]}/{repo[1]}")
                else:
                    GithubWatcher.cached[repo]['friend'] = GithubWatcher.cached[repo]['friend'] + [friend.id]
            if GithubWatcher.cached[repo]['last_id'] == -1:
                await GithubWatcher.github_schedule(app=app, manuel=True, per_page=1, page=1, repo=repo)
            success_count += 1
        res = [Plain(text=f"{success_count} 个仓库订阅成功")]
        if failed:
            res.append(Plain(text=f"\n{len(failed)} 个仓库订阅失败"
                                  f"\n失败的仓库有：{' '.join(failed)}"))
        if duplicated:
            res.append(Plain(text=f"\n{len(duplicated)} 个仓库已在订阅列表中"
                                  f"\n重复的仓库有：{' '.join(duplicated)}"))
        try:
            GithubWatcher.store_cache(manual=False)
            GithubWatcher.update_cache(manual=False)
            return MessageChain.create(res)
        except Exception as e:
            logger.error(e)
            res.append(Plain(text="\n\n刷新缓存失败"))
            return MessageChain.create(res)

    @staticmethod
    async def remove(**kwargs):
        """
        说明：
            移除订阅
        参数：
            :**kwarg arg: 仓库名，需以字符串形式传入
            :**kwarg group: Group 实例，默认为 None
            :**kwarg friend: Friend 实例，默认为 None
        """
        if not GithubWatcher.status:
            return MessageChain.create([Plain(text=f"Github 仓库订阅功能已关闭")])
        repos = None
        group = None
        friend = None
        for name, arg in kwargs.items():
            if name == "arg" and isinstance(arg, str):
                repos = arg
            if isinstance(arg, Group):
                group = arg
            if isinstance(arg, Friend):
                friend = arg
        if not group and not friend:
            return MessageChain.create([
                Plain(text=f"无法获取 Group 或 Friend 实例")
            ])
        if not repos:
            return MessageChain.create([
                Plain(text="未填写需要取消订阅的仓库")
            ])
        repos = repos.split(" ")
        failed = []
        success_count = 0
        for repo in repos:
            repo = repo.split("/")
            if len(repo) != 2:
                failed.append("/".join(repo))
                continue
            repo = (repo[0], repo[1])
            if repo not in GithubWatcher.cached.keys():
                failed.append("/".join(repo))
                continue
            if group:
                GithubWatcher.cached[repo]['group'] = [
                    group_id for group_id in GithubWatcher.cached[repo]['group'] if group_id != group.id
                ]
            if friend:
                GithubWatcher.cached[repo]['friend'] = [
                    friend_id for friend_id in GithubWatcher.cached[repo]['group'] if friend_id != friend.id
                ]
            if not (GithubWatcher.cached[repo]['group'] and GithubWatcher.cached[repo]['friend']):
                GithubWatcher.cached.pop(repo)
            success_count += 1
        res = [Plain(text=f"{success_count} 个仓库取消订阅成功")]
        if failed:
            res.append(Plain(text=f"\n{len(failed)} 个仓库取消订阅失败"
                                  f"\n失败的仓库有：{' '.join(failed)}"))
        try:
            GithubWatcher.store_cache(manual=False)
            GithubWatcher.update_cache(manual=False)
            return MessageChain.create(res)
        except Exception as e:
            logger.error(e)
            res.append(Plain(text="\n\n刷新缓存失败"))
            return MessageChain.create(res)

    @staticmethod
    async def cache(**kwargs):
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
            return GithubWatcher.update_cache(manual=True)
        if command == 'store':
            return GithubWatcher.store_cache(manual=True)
        """
        说明：
            更新缓存
        参数：
            :**kwarg command: 功能，update 或 store
        """

    @staticmethod
    def update_cache(manual: bool = False):
        """
        说明：
            更新缓存
        参数：
            :param manual: 手动，为 True 则返回 MessageChain，为否则仅运行
        """
        try:
            with open(str(Path(__file__).parent.joinpath("watcher_data.json")), "r") as r:
                data = json.loads(r.read())
                cache = {}
                for key in data.keys():
                    owner, repo = key.split("/")
                    cache[(owner, repo)] = data[key]
                GithubWatcher.cached = cache
            return MessageChain.create([Plain(text="更新缓存成功")]) if manual else None
        except (FileNotFoundError, JSONDecodeError):
            return MessageChain.create([Plain(text="无法更新缓存，请检查是否删除了缓存文件并重新储存缓存")])

    @staticmethod
    def store_cache(manual: bool = False):
        """
        说明：
            储存缓存
        参数：
            :param manual: 手动，为 True 则返回 MessageChain，为否则仅运行
        """
        with open(str(Path(__file__).parent.joinpath("watcher_data.json")), "w") as w:
            cache = {}
            for key in GithubWatcher.cached.keys():
                new_key = f"{key[0]}/{key[1]}"
                cache[new_key] = GithubWatcher.cached[key]
            w.write(json.dumps(cache, indent=4))
        return MessageChain.create([Plain(text="写入缓存成功")]) if manual else None

    @staticmethod
    async def check(**kwargs) -> MessageChain:
        """
        说明：
            查询订阅
        参数：
            :**kwarg group: Group 实例，默认为 None
            :**kwarg friend: Friend 实例，默认为 None
        """
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
        watched = []
        target = group if group else friend
        field = 'group' if group else 'friend'
        for repo in GithubWatcher.cached.keys():
            if target.id in GithubWatcher.cached[repo][field]:
                watched.append(f"{repo[0]}/{repo[1]}")
        res = [Plain(text=f"{'本群' if group else '你'}订阅的仓库有：\n"
                          f"{' '.join(watched)}")]
        return MessageChain.create(res)

    @staticmethod
    async def get_repo_event(app: Ariadne, repo: tuple, per_page: int = 30, page: int = 1):
        """
        说明：
            取得 GitHub 中某个仓库的 events
        参数：
            :param app: Ariadne
            :param repo: 形如 (SAGIRI-kawaii, sagiri-bot) 的仓库名
            :param per_page: [可选] 取得特定数量的 events，默认取 30 个
            :param page: [可选] 取得特定页数的 events，默认取第一页
        """
        url = GithubWatcher.base_url \
              + GithubWatcher.events_url.replace('{owner}', repo[0]).replace('{repo}', repo[1]) \
              + f'?per_page={per_page}&page={page}'
        try:
            res = await GithubWatcher.session.get(url=url)
            res = await res.json()
            return res
        except Exception as e:
            logger.error(e)
            if groups := GithubWatcher.cached[repo]['group']:
                for group in groups:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"无法取得仓库 {repo[0]}/{repo[1]} 的更新，将跳过该仓库。")
                    ]))
            if groups := GithubWatcher.cached[repo]['friend']:
                for group in groups:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"无法取得仓库 {repo[0]}/{repo[1]} 的更新，将跳过该仓库。")
                    ]))
            GithubWatcher.cached[repo]['enabled'] = False
            return None

    @staticmethod
    async def a_generate_plain(event: dict):
        """
        说明：
            异步 生成 Plain
        参数：
            :param event: 从 GitHub API /repo/{owner}/{repo}/events 所取得列表中的任意一项
        """
        return await asyncio.get_event_loop().run_in_executor(None, GithubWatcher.generate_plain, event)

    @staticmethod
    def generate_plain(event: dict):
        """
        说明：
            生成 Plain
        参数：
            :param event: 从 GitHub API /repo/{owner}/{repo}/events 所取得列表中的任意一项
        """
        actor = event['actor']['display_login']
        event_time = datetime.fromisoformat(event['created_at'] + '+08:00') \
            .strftime('%Y-%m-%d %H:%M:%S')
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
                return Plain(text=f"----------\n"
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
                return Plain(text=f"----------\n"
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
                return Plain(text=f"----------\n"
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
            commits = []
            for commit in event['payload']['commits']:
                commits.append(f"· [{commit['author']['name']}] {commit['message']}")
            return Plain(text=f"----------\n"
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
            return Plain(text=f"----------\n"
                              f"[新 Comment]\n"
                              f"{body}"
                              f"\n"
                              f"发布人：{actor}\n"
                              f"时间：{event_time}\n"
                              f"链接：{link}\n")
        return None

    @staticmethod
    async def github_schedule(**kwargs):
        """
        说明：
            GitHub 定时工具
        参数：
            :**kwarg app: Ariadne 实例
            :**kwarg manual: [可选] 手动，为 True 则返回 MessageChain，为否则直接发送
            :**kwarg per_page: [可选] 取得特定数量的 events，默认取 30 个
            :**kwarg page: [可选] 取得特定页数的 events，默认取第一页
        """
        if GithubWatcher.is_running:
            return None
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
            e = "无法获得 Ariadne 实例"
            logger.error(e)
            return None
        if GithubWatcher.status and repo:
            res = []
            if events := await GithubWatcher.get_repo_event(app, repo, per_page, page):
                GithubWatcher.cached[repo]['last_id'] = int(events[0]['id'])
                if resp := await GithubWatcher.a_generate_plain(events[0]):
                    res.append(resp)
            if not res:
                return None
            res.insert(0, Plain(text=f"仓库：{repo[0]}/{repo[1]}\n"))
            res.append(Plain(text=f"----------\n"
                                  f"获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
            return MessageChain.create(res)
        if GithubWatcher.status and not GithubWatcher.is_running:
            GithubWatcher.is_running = True
            for repo in GithubWatcher.cached.keys():
                if not GithubWatcher.cached[repo]['enabled']:
                    print('continued')
                    continue
                res = []
                if events := await GithubWatcher.get_repo_event(app, repo, per_page, page):
                    last_id = GithubWatcher.cached[repo]['last_id']
                    new_last_id = last_id
                    for index, event in enumerate(events):
                        if index == 0:
                            new_last_id = int(event['id'])
                        if int(event['id']) <= last_id:
                            break
                        if resp := await GithubWatcher.a_generate_plain(event):
                            res.append(resp)
                        else:
                            continue
                    GithubWatcher.cached[repo]['last_id'] = new_last_id
                if res:
                    res.insert(0, Plain(text=f"仓库：{repo[0]}/{repo[1]}\n"))
                    res.append(Plain(text=f"----------\n"
                                          f"获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
                    # res = await MessageChainUtils.messagechain_to_img(MessageChain.create(res))
                    res = MessageChain.create(res)
                    if manual:
                        GithubWatcher.is_running = False
                        return MessageItem(res, Normal())
                    for group in GithubWatcher.cached[repo]['group']:
                        try:
                            await app.sendGroupMessage(group, res)
                        except (AccountMuted, UnknownTarget):
                            pass
                    for friend in GithubWatcher.cached[repo]['friend']:
                        try:
                            await app.sendFriendMessage(friend, res)
                        except UnknownTarget:
                            pass
            GithubWatcher.store_cache()
            GithubWatcher.is_running = False
        else:
            if manual:
                return MessageItem(MessageChain.create([Plain(text=f"Github 订阅功能已关闭。")]), QuoteSource())


@scheduler.schedule(crontabify("*/15 * * * *"))
async def github_schedule(app: Ariadne):
    try:
        await GithubWatcher.github_schedule(app=app, manual=False)
    except:
        pass
