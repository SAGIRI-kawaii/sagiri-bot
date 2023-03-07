import asyncio
from typing import Dict, Optional, Union

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter

from .gb import running_group, running_mutex
from .utils import StatisticType, update_member_statistic
from .wordle import Wordle, all_word

CE = {"CHS": "中译", "ENG": "英译"}


class WordleWaiter(Waiter.create([GroupMessage])):
    def __init__(
        self,
        account: int,
        wordle: Wordle,
        meaning: Dict[str, str],
        group: Union[Group, int],
        member: Optional[Union[Member, int]] = None,
    ):
        self.account = account
        self.wordle = wordle
        self.group = group if isinstance(group, int) else group.id
        self.meaning = meaning
        self.meaning_str = "\n".join(
            f"{CE[e]}：{self.meaning[e]}" for e in CE if e in self.meaning
        )
        self.member = (
            (member if isinstance(member, int) else member.id) if member else None
        )
        self.member_list = set()
        self.member_list_mutex = asyncio.Lock()

    async def update_statistic(
        self, statistic: StatisticType, member: Union[Member, int]
    ):
        async with self.member_list_mutex:
            await update_member_statistic(self.group, member, statistic)

    async def remove_running(self):
        async with running_mutex:
            if self.group in running_group:
                running_group.remove(self.group)

    async def gameover(self, app: Ariadne, source: Source):
        await app.send_group_message(
            self.group,
            MessageChain(
                Image(data_bytes=self.wordle.get_img()),
                "很遗憾，没有人猜出来呢" f"单词：{self.wordle.word}\n{self.meaning_str}",
            ),
            quote=source,
        )

        async with self.member_list_mutex:
            for m in self.member_list:
                await update_member_statistic(
                    self.group, m, StatisticType.lose | StatisticType.game
                )
        await self.remove_running()

        return False

    async def detected_event(
        self,
        app: Ariadne,
        group: Group,
        member: Member,
        message: MessageChain,
        source: Source,
    ):
        # 判断是否是服务范围
        if self.group != group.id or (self.member and self.member != member.id) or self.account != app.account:
            return

        # 什么，放弃了？GiveUp!
        word = str(message).strip()
        if word in {"/wordle -giveup", "/wordle -g"}:
            return await self.gameover(app, source)

        if word == "/wordle -hint":
            await self.update_statistic(StatisticType.hint, member)
            await app.send_group_message(
                group,
                MessageChain(
                    Image(data_bytes=self.wordle.get_hint())
                    if self.wordle.guess_right_chars
                    else "你还没有猜对过一个字母哦~再猜猜吧~"
                ),
            )
            return True
        
        # 防止出现问题
        if self.wordle.finish:
            return False

        word = word.upper()
        # 应该是聊其他的，直接 return
        legal_chars = "'-./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if len(word) != self.wordle.length or not all(c in legal_chars for c in word):
            return

        async with self.member_list_mutex:
            self.member_list.add(member.id)

        if word not in all_word:
            await app.send_group_message(
                group,
                MessageChain(f"你确定 {word} 是一个合法的单词吗？"),
                quote=source,
            )
            return True
        elif word in self.wordle.history_words:
            await app.send_group_message(
                group, MessageChain("你已经猜过这个单词了呢"), quote=source
            )
            return True

        game_end, game_win = self.wordle.guess(word)

        if game_win:
            await self.update_statistic(StatisticType.correct, member)
            for m in self.member_list:
                await self.update_statistic(StatisticType.win | StatisticType.game, m)

            await app.send_group_message(
                group,
                MessageChain(
                    Image(data_bytes=self.wordle.get_img()),
                    f"\n恭喜你猜出了单词！\n【单词】：{self.wordle.word}\n{self.meaning_str}",
                ),
                quote=source,
            )
            await self.remove_running()
            return False
        elif game_end:
            await self.update_statistic(StatisticType.wrong, member)
            return (
                await self.gameover(app, source) if group.id in running_group else False
            )
        else:
            await app.send_group_message(
                group, MessageChain(Image(data_bytes=self.wordle.get_img()))
            )
            await self.update_statistic(StatisticType.wrong, member)
            return True
