import os
import jinja2
import random
import base64
from pathlib import Path

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from shared.utils.text2img import template2img
from shared.models.saya_data import get_saya_data
from shared.utils.module_related import get_command
from shared.models.config import load_plugin_meta_by_module
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

saya = Saya.current()
channel = Channel.current()

channel.name("Helper")
channel.author("SAGIRI-kawaii")
channel.description("一个获取帮助的插件，在群中发送 `/help` 即可")

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        Path(__file__).parent / "templates"
    ),
    enable_async=True,
    autoescape=True,
)
TEMPLATE_PATH = Path(__file__).parent / "templates"
BANNER_PATH = Path(__file__).parent / "banners"


def judge(name: str, group: int | Group):
    group = group.id if isinstance(group, Group) else group
    group = str(group)
    saya_data = get_saya_data()
    if name not in saya_data.switch:
        print(name, "not found!")
        saya_data.add_saya(name)
    if group not in saya_data.switch[name]:
        saya_data.add_group(group)
    return saya_data.is_turned_on(name, group)


def random_pic(base_path: Path | str) -> str:
    if isinstance(base_path, str):
        base_path = Path(base_path)
    path_dir = os.listdir(base_path)
    path = random.sample(path_dir, 1)[0]
    return f"data:image/png;base64,{base64.b64encode((Path(__file__).parent / 'banners' / path).read_bytes()).decode()}"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("helper", 1),
            Function.require(channel.module, response_administrator=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def helper(app: Ariadne, group: Group, source: Source):
    modules = []
    for i, c in enumerate(sorted(saya.channels)):
        plugin_meta = load_plugin_meta_by_module(c)
        modules.append((
            i + 1,
            plugin_meta.display_name or saya.channels[c].meta["name"] or c.split(".")[-1],
            judge(c, group),
            plugin_meta.maintaining or False
        ))

    if len(modules) % 3:
        modules.extend([(None, None, None, None) for _ in range(3 - len(modules) % 3)])
    img = await template2img(
        TEMPLATE_PATH / "plugins.html",
        {
            "settings": modules,
            "banner": random_pic(BANNER_PATH),
            "title": "SAGIRI-BOT帮助菜单",
            "subtitle": "CREATED BY SAGIRI-BOT"
        }
    )
    await app.send_group_message(group, MessageChain(Image(data_bytes=img)), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch("[0-9]+$") @ "index"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("helper", 1),
            Function.require(channel.module, response_administrator=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def detail_helper(app: Ariadne, group: Group, source: Source, index: RegexResult):
    index = int(index.result.display)
    channels = sorted(saya.channels)
    if index > len(channels):
        return await app.send_group_message(
            group,
            MessageChain(f"一共只有{len(channels)}个插件捏，怎么到你这里变成{index}了，真是的，太粗心了啦！"),
            quote=source
        )
    elif index == 0:
        return await app.send_group_message(
            group,
            MessageChain("0？我看你像个零！"),
            quote=source
        )
    else:
        module = channels[index - 1]
        plugin_meta = load_plugin_meta_by_module(module)
        img = await template2img(
            (TEMPLATE_PATH / "plugin_detail.html").read_text(encoding="utf-8"),
            {
                "display_name": plugin_meta.display_name or saya.channels[module].meta["name"],
                "module": module,
                "banner": random_pic(BANNER_PATH),
                "authors": plugin_meta.authors or ["暂无"],
                "description": plugin_meta.description or "暂无",
                "usage": "\n".join(plugin_meta.usage) or "暂无",
                "example": "\n".join(plugin_meta.example) or "暂无",
                "maintaining": plugin_meta.maintaining or False
            }
        )
        await app.send_group_message(group, MessageChain(Image(data_bytes=img)), quote=source)
