import jinja2
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
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("Helper")
channel.author("SAGIRI-kawaii")
channel.description("一个获取英文缩写意思的插件，在群中发送 `缩 内容` 即可")

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(r"W:\Python workspace\RE-SAGIRIBOT\sagiri_bot\handler\required_module\helper"),
    enable_async=True,
    autoescape=True
)

saya_data_instance = None


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
    print(name, group, saya_data.is_turned_on(name, group))
    return saya_data.is_turned_on(name, group)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("info")])],
        decorators=[
            FrequencyLimit.require("helper", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def helper(app: Ariadne, group: Group, source: Source):
    modules = [
        (saya.channels[c].meta['name'] if saya.channels[c].meta['name'] else c.split('.')[-1], judge(c, group))
        for c in saya.channels
    ]
    if len(modules) % 15:
        modules.extend([(None, None) for _ in range(15 - len(modules) % 15)])
    print(modules)
    template = env.get_template("group_info_template.html")
    root_div_width = (len(modules) // 25) * 520 + 60 if len(modules) % 25 else (len(modules) // 25) * 520 + 540
    html = await template.render_async(
        settings=modules,
        background_image=r"W:\Python workspace\RE-SAGIRIBOT\sagiri_bot\handler\required_module\helper\background.png",
        avatar=f"https://p.qlogo.cn/gh/{group.id}/{group.id}_1/",
        name=group.name,
        gid=group.id,
        count=len(await app.get_member_list(group)) + 1,
        root_div_width=root_div_width
    )
    await app.send_group_message(
        group,
        MessageChain([Image(data_bytes=await html_to_pic(html, wait=0, viewport={"width": 1920, "height": 1080}))]),
        quote=source
    )
