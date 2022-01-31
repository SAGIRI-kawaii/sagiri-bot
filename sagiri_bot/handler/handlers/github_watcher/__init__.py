from graia.ariadne.app import Ariadne, Friend
from graia.ariadne.event.message import Group, Member, FriendMessage, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import MemberPerm
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.utils import user_permission_require
from .github_watcher import GithubWatcher

saya = Saya.current()
channel = Channel.current()

channel.name("GithubWatcher")
channel.author("nullqwertyuiop")
channel.description("/github-watch enable [3级权限]"
                    "/github-watch disable [3级权限]"
                    "/github-watch add {repo} [repo]+ [2级或管理员权限]"
                    "/github-watch remove {repo} [repo]+ [2级或管理员权限]"
                    "/github-watch check [任何人]"
                    "/github-watch cache {update/store} [2级或管理员权限]")


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def github_watcher_friend_handler(app: Ariadne, message: MessageChain, friend: Friend):
    if result := await GithubWatcherEntryPoint.real_handle(app, message, friend=friend):
        await MessageSender(result.strategy).send(app, result.message, message, friend, friend)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def github_watcher_group_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await GithubWatcherEntryPoint.real_handle(app, message, group=group, member=member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class GithubWatcherEntryPoint(AbstractHandler):
    __name__ = "GithubWatcherEntryPoint"
    __description__ = "Github 订阅 Handler"
    __usage__ = "None"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        pass

    @staticmethod
    @switch()
    @blacklist()
    async def real_handle(app: Ariadne, message: MessageChain, group: Group = None,
                          member: Member = None, friend: Friend = None) -> MessageItem:
        commands = {
            "enable": {
                "permission": [3, []],
                "manual": "/github-watch enable",
                "description": "启用 Github 订阅功能",
                "func": GithubWatcher.enable
            },
            "disable": {
                "permission": [3, []],
                "manual": "/github-watch disable",
                "description": "禁用 Github 订阅功能",
                "func": GithubWatcher.disable
            },
            "add": {
                "permission": [2, (MemberPerm.Administrator, MemberPerm.Owner)],
                "manual": "/github-watch add {repo} [repo]+",
                "description": "订阅仓库变动，可同时订阅多个仓库",
                "func": GithubWatcher.add
            },
            "remove": {
                "permission": [2, (MemberPerm.Administrator, MemberPerm.Owner)],
                "manual": "/github-watch remove {repo} [repo]+",
                "description": "取消订阅仓库变动，可同时取消订阅多个仓库",
                "func": GithubWatcher.remove
            },
            "check": {
                "permission": [1, (MemberPerm.Member, MemberPerm.Administrator, MemberPerm.Owner)],
                "manual": "/github-watch check",
                "description": "手动查看仓库订阅列表",
                "func": GithubWatcher.check
            },
            "cache": {
                "permission": [2, (MemberPerm.Administrator, MemberPerm.Owner)],
                "manual": "/github-watch cache {update/store}",
                "description": "更新/储存缓存",
                "func": GithubWatcher.cache
            }
        }
        if message.asDisplay().startswith("/github-watch"):
            if not GithubWatcher.initialize:
                GithubWatcher.update_cache()
                GithubWatcher.initialize = True
            args = message.asDisplay().split(" ", maxsplit=1)
            if len(args) == 1:
                ...
            _, args = args
            name = args.split(" ", maxsplit=1)[0]
            arg = ''.join(args.split(" ", maxsplit=1)[1:])
            if name not in commands.keys():
                return MessageItem(MessageChain.create([Plain(text=f"未知指令：{arg}")]), QuoteSource())
            if member and group:
                permission = commands[name]['permission']
                if not await user_permission_require(group, member, permission[0]) \
                        and not (member.permission in permission[1]):
                    return MessageItem(MessageChain.create([Plain(
                        text=f"权限不足，你需要 {permission[0]} 级权限"
                             f"{('或来自 ' + str(permission[1][0]) + ' 的权限') if permission[1] else ''}")]), QuoteSource())
            arg = arg.strip()
            return MessageItem(await commands[name]['func'](
                app=app, group=group, friend=friend, arg=arg
            ), QuoteSource())
