from enum import Flag, auto
from sqlalchemy import select
from typing import Union, Tuple

from graia.ariadne.model import Group, Member

from sagiri_bot.orm.async_orm import orm, WordleStatistic


class StatisticType(Flag):
    win = auto()
    lose = auto()
    wrong = auto()
    correct = auto()
    game = auto()
    hint = auto()


count = {
    "win_count": StatisticType.win,
    "lose_count": StatisticType.lose,
    "correct_count": StatisticType.correct,
    "wrong_count": StatisticType.wrong,
    "game_count": StatisticType.game,
    "hint_count": StatisticType.hint,
}


async def update_member_statistic(
    group: Union[int, Group],
    member: Union[int, Member],
    statistic_type: StatisticType,
    value: int = 1,
):
    if isinstance(member, Member):
        member = member.id
    if isinstance(group, Group):
        group = group.id

    old_value = await get_member_statistic(group, member)

    new_value = {"group_id": group, "member_id": member}
    for num, (name, stype) in enumerate(count.items()):
        if stype in statistic_type:
            new_value[name] = old_value[num] + value

    await orm.insert_or_update(
        WordleStatistic,
        [WordleStatistic.member_id == member, WordleStatistic.group_id == group],
        new_value,
    )


async def get_member_statistic(
    group: Union[int, Group], member: Union[int, Member]
) -> Tuple:
    if isinstance(member, Member):
        member = member.id
    if isinstance(group, Group):
        group = group.id
    if data := await orm.fetchone(
        select(
            WordleStatistic.win_count,
            WordleStatistic.lose_count,
            WordleStatistic.correct_count,
            WordleStatistic.wrong_count,
            WordleStatistic.game_count,
            WordleStatistic.hint_count,
        ).where(WordleStatistic.member_id == member, WordleStatistic.group_id == group)
    ):
        return data
    else:
        return 0, 0, 0, 0, 0, 0
