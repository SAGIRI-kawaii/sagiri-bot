import os
import json
import random
from pathlib import Path
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema

from sagiri_bot.internal_utils import get_command
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("Tarot")
channel.author("SAGIRI-kawaii")
channel.description("可以抽塔罗牌的插件，在群中发送 `塔罗牌` 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            FrequencyLimit.require("tarot", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def tarot(app: Ariadne, group: Group, source: Source):
    await app.send_group_message(group, Tarot.get_tarot(), quote=source)


class Tarot(object):
    @staticmethod
    def get_tarot() -> MessageChain:
        card, filename = Tarot.get_random_tarot()
        card_dir = random.choice(["normal", "reverse"])
        card_type = "正位" if card_dir == "normal" else "逆位"
        content = f"{card['name']} ({card['name-en']}) {card_type}\n牌意：{card['meaning'][card_dir]}"
        elements = []
        img_path = f"{os.getcwd()}/statics/tarot/{card_dir}/{filename}.jpg"
        if filename and os.path.exists(img_path):
            elements.append(Image(path=img_path))
        elements.append(Plain(text=content))
        return MessageChain(elements)

    @staticmethod
    def get_random_tarot():
        path = Path(os.getcwd()) / "statics" / "tarot" / "tarot.json"
        with open(path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        kinds = ["major", "pentacles", "wands", "cups", "swords"]
        cards = []
        for kind in kinds:
            cards.extend(data[kind])
        card = random.choice(cards)
        filename = next(
            (
                "{}{:02d}".format(kind, card["num"])
                for kind in kinds
                if card in data[kind]
            ),
            "",
        )

        return card, filename
