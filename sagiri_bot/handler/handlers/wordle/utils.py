from enum import Enum
from sqlalchemy import select
from typing import Union, Tuple

from graia.ariadne.model import Group, Member

from sagiri_bot.orm.async_orm import orm, WordleStatistic


class StatisticType(Enum):
    win = "win"
    lose = "lose"
    wrong = "wrong"
    correct = "correct"
    game = "game"
    hint = "hint"


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
    old_value = await orm.fetchone(
        select(
            WordleStatistic.win_count,
            WordleStatistic.lose_count,
            WordleStatistic.correct_count,
            WordleStatistic.wrong_count,
            WordleStatistic.game_count,
            WordleStatistic.hint_count,
        ).where(WordleStatistic.member_id == member, WordleStatistic.group_id == group)
    )
    if statistic_type == StatisticType.win:
        new_value_dict = {"win_count": old_value[0] + value if old_value else value}
    elif statistic_type == StatisticType.lose:
        new_value_dict = {"lose_count": old_value[1] + value if old_value else value}
    elif statistic_type == StatisticType.correct:
        new_value_dict = {"correct_count": old_value[2] + value if old_value else value}
    elif statistic_type == StatisticType.wrong:
        new_value_dict = {"wrong_count": old_value[3] + value if old_value else value}
    elif statistic_type == StatisticType.game:
        new_value_dict = {"game_count": old_value[4] + value if old_value else value}
    elif statistic_type == StatisticType.hint:
        new_value_dict = {"hint_count": old_value[5] + value if old_value else value}
    else:
        raise ValueError(f"Unknown statistic_type: {statistic_type}")
    new_value_dict["group_id"] = group
    new_value_dict["member_id"] = member
    await orm.insert_or_update(
        WordleStatistic,
        [WordleStatistic.member_id == member, WordleStatistic.group_id == group],
        new_value_dict,
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
