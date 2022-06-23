import os
import json

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import RegexMatch, UnionMatch, FullMatch, RegexResult

from .pool_data import init_pool_list
from sagiri_bot.utils import user_permission_require
from .gacha import gacha_info, FILE_PATH, Gacha, POOL
from utils.daily_number_limiter import DailyNumberLimiter
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
loop = bcc.loop

channel.name("GenshinGacha")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个原神抽卡插件\n"
    "在群中发送 `原神(10|90|180)连?抽?` 即可进行抽卡\n"
    "在群中发送 `原神(卡池|up|UP)(信息)?` 即可查看目前卡池信息\n"
    "在群中发送 `原神(卡池切换|切换卡池) {pool_name}` 即可切换当前卡池（管理）\n"
    "在群中发送 `更新原神卡池` 即可更新卡池信息（管理）"
)

group_pool = {
    # 这个字典保存每个群对应的卡池是哪个，群号字符串为key,卡池名为value，群号不包含在字典key里卡池按默认DEFAULT_POOL
}

Gacha10Limit = 10  # 10连每天可以抽的次数
Gacha90Limit = 10  # 90连每天可以抽的次数
Gacha180Limit = 10  # 180连每天可以抽的次数

daily_limiter_10 = DailyNumberLimiter(Gacha10Limit)
daily_limiter_90 = DailyNumberLimiter(Gacha90Limit)
daily_limiter_180 = DailyNumberLimiter(Gacha180Limit)


def save_group_pool():
    with open(os.path.join(FILE_PATH, 'gid_pool.json'), 'w', encoding='UTF-8') as w:
        json.dump(group_pool, w, ensure_ascii=False)


# 检查gid_pool.json是否存在，没有创建空的
if not os.path.exists(os.path.join(FILE_PATH, 'gid_pool.json')):
    save_group_pool()

# 读取gid_pool.json的信息
with open(os.path.join(FILE_PATH, 'gid_pool.json'), 'r', encoding='UTF-8') as f:
    group_pool = json.load(f)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([RegexMatch(r"原神"), RegexMatch(r"(10|90|180)") @ "count", RegexMatch(r"连?抽?") @ "suffix"])
        ],
        decorators=[
            FrequencyLimit.require("gacha", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def gacha(app: Ariadne, group: Group, message: MessageChain, member: Member, count: RegexResult):
    gid = group.id
    user_id = member.id
    count = int(count.result.asDisplay())
    if all([
        count == 10 and not daily_limiter_10.check(user_id),
        count == 90 and not daily_limiter_90.check(user_id),
        count == 180 and not daily_limiter_180.check(user_id)
    ]):
        await app.sendMessage(group, MessageChain.create([Plain(text='今天已经抽了很多次啦，明天再来吧~')]))
        return
    if gid in group_pool:
        G = Gacha(group_pool[gid])
    else:
        G = Gacha()
    if count == 10:
        daily_limiter_10.increase(user_id)
    elif count == 90:
        daily_limiter_90.increase(user_id)
    else:
        daily_limiter_180.increase(user_id)
    await app.sendMessage(
        group,
        G.gacha_10() if count == 10 else (G.gacha_90() if count == 90 else G.gacha_90(180)),
        quote=message.getFirst(Source)
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"原神(卡池|up|UP)(信息)?$")])]
    )
)
async def get_gacha_info(app: Ariadne, group: Group):
    gid = group.id
    info = gacha_info(group_pool[gid]) if gid in group_pool else gacha_info()
    await app.sendMessage(group, info)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([UnionMatch("原神卡池切换", "原神切换卡池"), RegexMatch(r".+") @ "pool_name"])],
        decorators=[
            Function.require(channel.module),
            BlackListControl.enable()
        ]
    )
)
async def set_pool(app: Ariadne, group: Group, message: MessageChain, member: Member, pool_name: RegexResult):
    if not await user_permission_require(group, member, 2):
        await app.sendMessage(group, MessageChain('只有群管理才能切换卡池'), quote=message.getFirst(Source))
        return

    pool_name = pool_name.result.asDisplay().strip()
    gid = group.id

    if pool_name in POOL.keys():
        if gid in group_pool:
            group_pool[gid] = pool_name
        else:
            group_pool.setdefault(gid, pool_name)
        save_group_pool()
        await app.sendMessage(group, MessageChain(f"卡池已切换为 {pool_name} "))
        return

    txt = "请使用以下命令来切换卡池\n"
    for i in POOL.keys():
        txt += f"原神卡池切换 {i} \n"
    await app.sendMessage(group, MessageChain(txt))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("更新原神卡池")])],
        decorators=[
            Function.require(channel.module, notice=True),
            BlackListControl.enable()
        ]
    )
)
async def up_pool_(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if not await user_permission_require(group, member, 3):
        await app.sendMessage(group, MessageChain('只有群管理才能更新卡池'), quote=message.getFirst(Source))
        return
    await app.sendMessage(group, MessageChain('正在更新卡池'))
    _ = await init_pool_list()
    await app.sendMessage(group, MessageChain('更新卡池完成'))


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def update_pool():
    await init_pool_list()
