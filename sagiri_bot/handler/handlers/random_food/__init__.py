import json
import random
from pathlib import Path
from random import randrange

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, UnionMatch, MatchResult
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("RandomFood")
channel.author("nullqwertyuiop")
channel.description("随机餐点")

with open(str(Path(__file__).parent.joinpath("food.json")), "r", encoding="utf-8") as r:
    food = json.loads(r.read())


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                RegexMatch(r"[随隨][机機]"),
                UnionMatch("早餐", "午餐", "晚餐") @ "option"
            ])
        ],
        decorators=[
            FrequencyLimit.require("random_food", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def random_meal(app: Ariadne, message: MessageChain, group: Group, option: MatchResult):
    option = option.result.asDisplay()
    main_amount = 1 if option == "早餐" else 2
    dish = []
    if randrange(101) < 5:
        return "没得吃！"
    if randrange(2) if option != "午餐" else 1:
        dish.append(random.choice(food[option]["drink"]))
    if randrange(2) if option != "午餐" else 1:
        dish.append(random.choice(food[option]["pre"]))
    if not dish:
        if randrange(2):
            dish.append(random.choice(food[option]["drink"]))
        else:
            dish.append(random.choice(food[option]["pre"]))
    for i in range(0, main_amount):
        dish.append(random.choice(food[option]["main"]))
    result = f"你的随机{option}是：\n" + " ".join(dish)
    await app.sendGroupMessage(group, MessageChain(result), quote=message.getFirst(Source))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                RegexMatch(r"[随隨][机機]"),
                UnionMatch("奶茶", "果茶") @ "option"
            ])
        ],
        decorators=[
            FrequencyLimit.require("random_food", 2),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def random_tea(app: Ariadne, message: MessageChain, group: Group, option: MatchResult):
    option = option.result.asDisplay()
    if randrange(101) < 5:
        return "没得喝！"
    body = random.choice(food[option]["body"])
    addon = ""
    cream = ""
    temperature = random.choice(food[option]["temperature"])
    sugar = random.choice(food[option]["sugar"])
    divider = "加"
    for i in range(0, randrange(1, 4)):
        addon = divider + str(random.choice(food[option]["addon"]))
    if randrange(2):
        cream = divider + str(random.choice(food[option]["cream"]))
    result = f"你的随机{option}是：\n" + temperature + sugar + addon + cream + body
    await app.sendGroupMessage(group, MessageChain(result), quote=message.getFirst(Source))
