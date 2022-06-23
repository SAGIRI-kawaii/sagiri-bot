import asyncio
from loguru import logger
from asyncio import Semaphore
from typing import Union, Optional, NoReturn

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import FullMatch, ArgumentMatch, RegexMatch, RegexResult, ArgResult

from sagiri_bot.core.app_core import AppCore
from .wordle import Wordle, word_list, word_dics
from .utils import update_member_statistic, StatisticType, get_member_statistic
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("Wordle")
channel.author("SAGIRI-kawaii")
channel.description("wordle猜单词游戏，发送 /wordle -h 查看帮助")

inc = InterruptControl(AppCore.get_core_instance().get_bcc())
mutex = Semaphore(1)

group_running = {}
group_word_dic = {}
DEFAULT_DIC = "CET4"


class TimeWaiter(Waiter.create([GroupMessage])):

    """ 超时Waiter """

    def __init__(self, wordle_instance: Wordle, group: Union[Group, int], member: Optional[Union[Member, int]] = None):
        self.wordle = wordle_instance
        self.group = group if isinstance(group, int) else group.id
        self.member = (member if isinstance(member, int) else member.id) if member else None


class WordleWaiter(Waiter.create([GroupMessage])):

    """ wordle Waiter """

    def __init__(self, wordle_instance: Wordle, group: Union[Group, int], member: Optional[Union[Member, int]] = None):
        self.wordle = wordle_instance
        self.group = group if isinstance(group, int) else group.id
        self.member = (member if isinstance(member, int) else member.id) if member else None
        self.member_list = set()
        self.member_list_mutex = Semaphore(1)

    async def detected_event(self, app: Ariadne, group: Group, member: Member, message: MessageChain):
        word = message.asDisplay().strip()
        message_source = message.getFirst(Source)
        if self.group == group.id and (self.member == member.id or not self.member):
            if message.asDisplay().strip() in ("/wordle -giveup", "/wordle -g"):
                dic = group_word_dic[group.id]
                word_data = word_list[dic][len(self.wordle.word)][self.wordle.word]
                explain = '\n'.join([f"【{key}】：{word_data[key]}" for key in word_data])
                await app.sendGroupMessage(
                    group,
                    MessageChain([
                        Image(data_bytes=self.wordle.get_board_bytes()),
                        Plain(
                            "很遗憾，没有人猜出来呢"
                            f"单词：{self.wordle.word}\n{explain}"
                        )
                    ]),
                    quote=message_source
                )
                await self.member_list_mutex.acquire()
                for member in self.member_list:
                    await update_member_statistic(group, member, StatisticType.lose)
                    await update_member_statistic(group, member, StatisticType.game)
                self.member_list_mutex.release()
                await mutex.acquire()
                group_running[group.id] = False
                mutex.release()
                return True
            if message.asDisplay().strip() == "/wordle -hint":
                await update_member_statistic(group, member, StatisticType.hint)
                hint = self.wordle.get_hint()
                if not hint:
                    await app.sendGroupMessage(
                        group, MessageChain("你还没有猜对过一个字母哦~再猜猜吧~"), quote=message.getFirst(Source)
                    )
                else:
                    await app.sendGroupMessage(
                        group, MessageChain([Image(data_bytes=self.wordle.draw_hint())]), quote=message.getFirst(Source)
                    )
                return False
            if len(word) == self.wordle.length and word.encode('utf-8').isalpha():
                await self.member_list_mutex.acquire()
                self.member_list.add(member.id)
                self.member_list_mutex.release()
                await self.wordle.draw_mutex.acquire()
                print("required")
                result = self.wordle.guess(word)
                print(result)
                print("released")
                self.wordle.draw_mutex.release()
                if not result:
                    return True
                if result[0]:
                    await update_member_statistic(
                        group, member, StatisticType.correct if result[1] else StatisticType.wrong
                    )
                    await self.member_list_mutex.acquire()
                    for member in self.member_list:
                        await update_member_statistic(
                            group, member, StatisticType.win if result[1] else StatisticType.lose
                        )
                        await update_member_statistic(group, member, StatisticType.game)
                    self.member_list_mutex.release()
                    dic = group_word_dic[group.id]
                    word_data = word_list[dic][len(self.wordle.word)][self.wordle.word]
                    explain = '\n'.join([f"【{key}】：{word_data[key]}" for key in word_data])
                    await app.sendGroupMessage(
                        group,
                        MessageChain([
                            Image(data_bytes=self.wordle.get_board_bytes()),
                            Plain(
                                f"\n{'恭喜你猜出了单词！' if result[1] else '很遗憾，没有人猜出来呢'}\n"
                                f"【单词】：{self.wordle.word}\n{explain}"
                            )
                        ]),
                        quote=message_source
                    )
                    await mutex.acquire()
                    group_running[group.id] = False
                    mutex.release()
                    return True
                elif not result[2]:
                    await app.sendGroupMessage(
                        group, MessageChain(f"你确定 {word} 是一个合法的单词吗？"), quote=message_source
                    )
                elif result[3]:
                    await app.sendGroupMessage(group, MessageChain("你已经猜过这个单词了呢"), quote=message_source)
                else:
                    await update_member_statistic(group, member, StatisticType.wrong)
                    await app.sendGroupMessage(
                        group, MessageChain([Image(data_bytes=self.wordle.get_board_bytes())]), quote=message_source
                    )
                return False


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/wordle"),
                ArgumentMatch("-single", action="store_true", optional=True) @ "single_game",
                ArgumentMatch("-group", action="store_true", optional=True) @ "group_game",
                RegexMatch(r"-(l|length)=[0-9]+", optional=True) @ "length",
                RegexMatch(r"-(d|dic)=\w+", optional=True) @ "dic",
                ArgumentMatch("-help", "-h", action="store_true", optional=True) @ "get_help",
                ArgumentMatch("-giveup", "-g", action="store_true", optional=True) @ "give_up",
                ArgumentMatch("-s", "-statistic", action="store_true", optional=True) @ "statistic"
            ])
        ],
        decorators=[
            FrequencyLimit.require("wordle", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def wordle(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    single_game: ArgResult,
    dic: RegexResult,
    length: ArgResult,
    get_help: ArgResult,
    give_up: ArgResult,
    statistic: ArgResult
) -> NoReturn:
    if get_help.matched:
        await app.sendGroupMessage(
            group,
            MessageChain(
                "Wordle文字游戏\n"
                "答案为指定长度单词，发送对应长度单词即可\n"
                "灰色块代表此单词中没有此字母\n"
                "黄色块代表此单词中有此字母，但该字母所处位置不对\n"
                "绿色块代表此单词中有此字母且位置正确\n"
                "猜出单词或用光次数则游戏结束\n"
                "发起游戏：/wordle -l=5 -d=SAT，其中-l/-length为单词长度，-d/-dic为指定词典，默认为5和CET4\n"
                "中途放弃：/wordle -g 或 /wordle -giveup\n"
                "查看数据统计：/wordle -s 或 /wordle -statistic\n"
                "查看提示：/wordle -hint\n"
                f"注：目前包含词典：{'、'.join(word_dics)}"
            )
        )
        return None
    if statistic.matched:
        data = await get_member_statistic(group, member)
        await app.sendGroupMessage(
            group,
            MessageChain(
                f"用户 {member.name}\n"
                f"共参与{data[4]}场游戏，其中胜利{data[0]}场，失败{data[1]}场\n"
                f"一共猜对{data[2]}次，猜错{data[3]}次，共使用过{data[5]}次提示，再接再厉哦~"
            ),
            quote=message.getFirst(Source)
        )
        return None
    if give_up.matched:
        return None
    await mutex.acquire()
    if group.id in group_running and group_running[group.id]:
        await app.sendGroupMessage(group, MessageChain("本群已有正在运行中的游戏实例，请等待本局游戏结束！"))
        mutex.release()
        return None
    else:
        if dic.matched:
            dic = dic.result.asDisplay().split('=')[1].strip()
            if dic not in word_dics:
                await app.sendGroupMessage(group, MessageChain(f"没有找到名为{dic}的字典！已有字典：{'、'.join(word_dics)}"))
                mutex.release()
                return None
            else:
                group_word_dic[group.id] = dic
        elif group.id not in group_word_dic:
            group_word_dic[group.id] = DEFAULT_DIC
        group_running[group.id] = True
        mutex.release()
    single = single_game.matched
    length = int(length.result.asDisplay().split('=')[1].strip()) if length.matched else 5
    if length not in word_list[group_word_dic[group.id]].keys():
        await app.sendGroupMessage(
            group, MessageChain(
                f"单词长度错误，词库中没有长度为{length}的单词=！"
                f"目前词库（{group_word_dic[group.id]}）中"
                f"只有长度为{'、'.join([str(i) for i in sorted(word_list[group_word_dic[group.id]].keys())])}的单词！"
            )
        )
        await mutex.acquire()
        group_running[group.id] = False
        mutex.release()
        return None
    wordle_instance = Wordle(length, dic=group_word_dic[group.id])
    logger.success(f"成功创建 Wordle 实例，单词为：{wordle_instance.word}")
    await app.sendGroupMessage(
        group,
        MessageChain([
            Image(data_bytes=wordle_instance.get_board_bytes()),
            Plain(f"\n你有{wordle_instance.row}次机会猜出单词，单词长度为{wordle_instance.length}，请发送单词")
        ]),
        quote=message.getFirst(Source)
    )
    game_end = False
    try:
        while not game_end:
            game_end = await inc.wait(WordleWaiter(wordle_instance, group, member if single else None), timeout=300)
    except asyncio.exceptions.TimeoutError:
        await app.sendGroupMessage(group, MessageChain("游戏超时，进程结束"), quote=message.getFirst(Source))
        await mutex.acquire()
        group_running[group.id] = False
        mutex.release()
