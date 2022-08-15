import os
import jinja2
import random
from pathlib import Path
from typing import Union
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.parser.twilight import FullMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema

from utils.html2pic import html_to_pic
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
channel.description("一个获取英文缩写意思的插件，在群中发送 `缩 内容` 即可")

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
        print(name, "not found!")
        saya_data.add_saya(name)
    if group not in saya_data.switch[name]:
        saya_data.add_group(group)
    return saya_data.is_turned_on(name, group)


def random_pic(base_path: Union[Path, str]) -> Path:
    if isinstance(base_path, str):
        base_path = Path(base_path)
    path_dir = os.listdir(base_path)
    path = random.sample(path_dir, 1)[0]
    return base_path / path


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("info")])],
        decorators=[
            FrequencyLimit.require("helper", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def helper(app: Ariadne, group: Group, source: Source):
    modules = [
        (
            saya.channels[c].meta["name"]
            if saya.channels[c].meta["name"]
            else c.split(".")[-1],
            judge(c, group),
        )
        for c in saya.channels
    ]
    if len(modules) % 3:
        modules.extend([(None, None) for _ in range(3 - len(modules) % 3)])
    template = env.get_template("plugin_detail.html")
    html = await template.render_async(
        settings=modules,
        banner=random_pic(BANNER_PATH),
        avatar=f"https://p.qlogo.cn/gh/{group.id}/{group.id}_1/",
        name=group.name,
        gid=group.id,
        count=len(await app.get_member_list(group)) + 1,
        title="SAGIRI-BOT帮助菜单",
        subtitle="CREATED BY SAGIRI-BOT"
    )
    await app.send_group_message(
        group,
        MessageChain(
            [
                Image(
                    data_bytes=await html_to_pic(
                        html, wait=0, viewport={"width": 1000, "height": 1080}
                    )
                )
            ]
        ),
        quote=source,
    )
