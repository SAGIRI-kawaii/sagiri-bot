import json
import random
import asyncio

from graia.saya import Channel, Saya
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import ArgResult, ArgumentMatch, Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from shared.utils.control import (
    Distribute,
    BlackListControl,
    FrequencyLimit,
    Function,
    UserCalledCountControl
)
from shared.utils.module_related import get_command

from .gb import running_group, running_mutex
from .utils import get_member_statistic
from .waiter import WordleWaiter
from .wordle import Wordle, word_dic, word_path

saya = Saya.current()
channel = Channel.current()

channel.name("Wordle")
channel.author("SAGIRI-kawaii, I_love_study")
channel.description("wordle猜单词游戏，发送 /wordle -h 查看帮助")

assert saya.broadcast is not None
inc = InterruptControl(saya.broadcast)

DEFAULT_DIC = "CET4"

decorators = [
    Distribute.distribute(),
    FrequencyLimit.require("wordle", 2),
    Function.require(channel.module, notice=True),
    BlackListControl.enable(),
    UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
]


# 你肯定好奇为什么会有一个 @ "_"，因为这涉及到一个bug
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-help", "-h", action="store_true", optional=False)
                @ "_",
            ])
        ],
        decorators=decorators,
    )
)
async def wordle_help(app: Ariadne, group: Group):
    await app.send_group_message(
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
            f"注：目前包含词典：{'、'.join(word_dic)}"
        ),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch(
                    "-s", "-statistic", action="store_true", optional=False
                )
                @ "_",
            ])
        ],
        decorators=decorators,
    )
)
async def wordle_statistic(app: Ariadne, group: Group, member: Member, source: Source):
    data = await get_member_statistic(group, member)
    await app.send_group_message(
        group,
        MessageChain(
            f"用户 {member.name}\n共参与{data[4]}场游戏，"
            f"其中胜利{data[0]}场，失败{data[1]}场\n"
            f"一共猜对{data[2]}次，猜错{data[3]}次，"
            f"共使用过{data[5]}次提示，再接再厉哦~"
        ),
        quote=source,
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-d", "-dic") @ "dic",
                ArgumentMatch("--single", action="store_true") @ "single",
                ArgumentMatch("-l", "--length") @ "length",
            ])
        ],
        decorators=decorators,
    )
)
async def wordle(
        app: Ariadne,
        group: Group,
        member: Member,
        source: Source,
        dic: ArgResult,
        single: ArgResult,
        length: ArgResult,
):
    # 判断是否开了
    async with running_mutex:
        if group.id in running_group:
            await app.send_group_message(
                group, MessageChain("诶，游戏不是已经开始了吗？等到本局游戏结束再开好不好")
            )
            return

    # 字典选择
    if dic.matched:
        if (choose_dic := str(dic.result)) not in word_dic:
            await app.send_group_message(
                group,
                MessageChain(
                    f"{choose_dic}是什么类型的字典啊，我不造啊\n" f"我只知道{'、'.join(word_dic)}"
                ),
            )
            return
    else:
        choose_dic = "CET4"

    dic_data = json.loads(
        (word_path / f"{choose_dic}.json").read_text(encoding="UTF-8")
    )

    # 长度选择
    if length.matched:
        ls = str(length.result)
        if not ls.isnumeric():
            await app.send_group_message(group, MessageChain(f"'{ls}'是数字吗？"))
            return
        l = int(ls)
    else:
        l = 5

    # 搜寻并决定单词
    choices = [k for k in dic_data if len(k) == l]
    if not choices:
        return await app.send_group_message(group, MessageChain("对不起呢，没有这种长度的单词"))

    guess_word = random.choice(choices)

    # 是否单人
    single_gamer = single.matched

    async with running_mutex:
        running_group.add(group.id)
    gaming = True

    w = Wordle(guess_word)
    logger.success(f"成功创建 Wordle 实例，单词为：{guess_word}")
    await app.send_group_message(group, MessageChain(Image(data_bytes=w.get_img())))

    try:
        while gaming:
            gaming = await inc.wait(
                WordleWaiter(
                    app.account,
                    w,
                    dic_data[guess_word],
                    group,
                    member if single_gamer else None,
                ),
                timeout=300,
            )
    except asyncio.exceptions.TimeoutError:
        await app.send_group_message(group, MessageChain("游戏超时，进程结束"), quote=source)
        async with running_mutex:
            running_group.remove(group.id)
