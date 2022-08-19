import asyncio
from typing import Dict, Union, Optional

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Plain, Image, Source
from graia.ariadne.event.message import Group, Member, GroupMessage

from .wordle import Wordle, all_word
from .utils import update_member_statistic, StatisticType
from .gb import running_group, running_mutex

CE = {"CHS": "中译", "ENG": "英译"}


class WordleWaiter(Waiter.create([GroupMessage])):
    def __init__(
        self,
        wordle: Wordle,
        meaning: Dict[str, str],
        group: Union[Group, int],
        member: Optional[Union[Member, int]] = None,
    ):
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
                await update_member_statistic(self.group, m, StatisticType.lose)
                await update_member_statistic(self.group, m, StatisticType.game)
        async with running_mutex:
            running_group.remove(self.group)

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
        if self.group != group.id or (self.member and self.member != member.id):
            return True

        word = str(message).strip()
        if word in ("/wordle -giveup", "/wordle -g"):
            return await self.gameover(app, source)

        if word == "/wordle -hint":
            await update_member_statistic(group, member, StatisticType.hint)
            if not self.wordle.guess_right_chars:
                await app.send_group_message(
                    group, MessageChain("你还没有猜对过一个字母哦~再猜猜吧~"), quote=source
                )
            else:
                await app.send_group_message(
                    group,
                    MessageChain(Image(data_bytes=self.wordle.get_hint())),
                    quote=source,
                )
            return True

        if len(word) != self.wordle.length or not word.isalpha():
            return True

        async with self.member_list_mutex:
            self.member_list.add(member.id)

        word = word.upper()

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
            async with self.member_list_mutex:
                await update_member_statistic(group, member, StatisticType.correct)
                for m in self.member_list:
                    await update_member_statistic(group, m, StatisticType.win)
                    await update_member_statistic(group, m, StatisticType.game)

            await app.send_group_message(
                group,
                MessageChain(
                    Image(data_bytes=self.wordle.get_img()),
                    f"\n恭喜你猜出了单词！\n【单词】：{self.wordle.word}\n{self.meaning_str}",
                ),
                quote=source,
            )
            async with running_mutex:
                running_group.remove(group.id)
            return False
        elif game_end:
            async with self.member_list_mutex:
                await update_member_statistic(group, member, StatisticType.wrong)
            return await self.gameover(app, source)
        else:
            await app.send_group_message(
                group, MessageChain(Image(data_bytes=self.wordle.get_img()))
            )
            async with self.member_list_mutex:
                await update_member_statistic(group, member, StatisticType.wrong)
            return True
