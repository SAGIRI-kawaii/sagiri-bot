import os
import jinja2
import random
from pathlib import Path
from typing import Union
from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from utils.html2pic import html_to_pic
from sagiri_bot.internal_utils import get_command
from sagiri_bot.config import load_plugin_meta_by_module
from sagiri_bot.handler.required_module.saya_manager.utils import saya_data
from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
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

saya_data_instance = None
BANNER_PATH = Path(__file__).parent / "banners"


def get_saya_data():
    global saya_data_instance
    if not saya_data_instance:
        saya_data_instance = saya_data
    return saya_data_instance


def judge(name: str, group: Union[int, Group]):
    group = group.id if isinstance(group, Group) else group
    group = str(group)
    if name not in saya_data.switch:
        logger.info(f"{name} not found!")
        saya_data.add_saya(name)
    if group not in saya_data.switch[name]:
        saya_data.add_group(group)
    return saya_data.is_turned_on(name, group)


def random_pic(base_path: Union[Path, str]) -> Union[str, Path]:
    if isinstance(base_path, str):
        base_path = Path(base_path)
    path_dir = os.listdir(base_path)
    path = random.sample(path_dir, 1)[0]
    return str(Path(__file__).parent / "banners" / path)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module)])],
        decorators=[
            FrequencyLimit.require("helper", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def helper(app: Ariadne, group: Group, source: Source):
    modules = []
    for i, c in enumerate(sorted(saya.channels)):
        plugin_meta = load_plugin_meta_by_module(c)
        modules.append(
            (
                i + 1,
                plugin_meta.display_name
                if plugin_meta.display_name else
                (
                    saya.channels[c].meta["name"]
                    if saya.channels[c].meta["name"]
                    else c.split(".")[-1]
                ),
                judge(c, group),
            )
        )
    if len(modules) % 3:
        modules.extend([(None, None, None) for _ in range(3 - len(modules) % 3)])
    template = env.get_template("plugins.html")
    html = await template.render_async(
        settings=modules,
        banner=random_pic(BANNER_PATH),
        title="SAGIRI-BOT帮助菜单",
        subtitle="CREATED BY SAGIRI-BOT"
    )
    await app.send_group_message(
        group,
        MessageChain([
            Image(
                data_bytes=await html_to_pic(
                    html, wait=0, viewport={"width": 1000, "height": 1080}
                )
            )
        ]),
        quote=source,
    )


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
            FrequencyLimit.require("helper", 1),
            Function.require(channel.module),
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
        template = env.get_template("plugin_detail.html")
        html = await template.render_async(
            display_name=plugin_meta.display_name or saya.channels[module]._name,
            module=module,
            banner=random_pic(BANNER_PATH),
            authors=plugin_meta.authors or ["暂无"],
            description=plugin_meta.description or "暂无",
            usage=plugin_meta.usage or "暂无",
            example=plugin_meta.example or "暂无"
        )
        await app.send_group_message(
            group,
            MessageChain([
                Image(
                    data_bytes=await html_to_pic(
                        html, wait=0, viewport={"width": 1000, "height": 1080}
                    )
                )
            ]),
            quote=source,
        )
