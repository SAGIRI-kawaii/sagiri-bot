import os
import re
import psutil
from typing import Match
from datetime import datetime

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, ArgumentMatch, ArgResult

from core import Sagiri
from shared.utils.time import sec_format
from shared.models.config import GlobalConfig
from shared.utils.control import Permission, Distribute

saya = Saya.current()
channel = Channel.current()

channel.name("SystemStatus")
channel.author("SAGIRI-kawaii")
channel.description("查看系统状态")

image_path = create(GlobalConfig).gallery
launch_time = create(Sagiri).launch_time


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/sys"),
                ArgumentMatch("-a", "-all", optional=True, action="store_true") @ "all_info",
                ArgumentMatch("-i", "-info", optional=True, action="store_true") @ "info",
                ArgumentMatch("-s", "-storage", optional=True, action="store_true") @ "storage"
            ])
        ],
        decorators=[Distribute.distribute(), Permission.require(Permission.SUPER_ADMIN)]
    )
)
async def system_status(app: Ariadne, group: Group, all_info: ArgResult, info: ArgResult, storage: ArgResult):
    mem = psutil.virtual_memory()
    total_memery = round(mem.total / 1024 ** 3, 2)
    launch_time_message = MessageChain(
        "SAGIRI-BOT\n"
        f"启动时间：{launch_time.strftime('%Y-%m-%d, %H:%M:%S')}\n"
        f"已运行时间：{sec_format((datetime.now() - launch_time).seconds, '{h}时{m}分{s}秒')}"
    )
    memory_message = MessageChain(
        "内存相关：\n    "
        f"内存总大小：{total_memery}GB\n    "
        f"内存使用量：{round(mem.used / 1024 ** 3, 2)}GB / {total_memery}GB ({round(mem.used / mem.total * 100, 2)}%)\n    "
        f"内存空闲量：{round(mem.free / 1024 ** 3, 2)}GB / {total_memery}GB ({round(mem.free / mem.total * 100, 2)}%)"
    )
    cpu_message = MessageChain(
        "CPU相关：\n    "
        f"CPU 物理核心数：{psutil.cpu_count(logical=False)}\n    "
        f"CPU总体占用：{psutil.cpu_percent()}%\n    "
        f"CPU频率：{psutil.cpu_freq().current}MHz"
    )
    disk_message = MessageChain(
        "磁盘相关：\n    "
        "图库占用空间：\n        " +
        "\n        ".join(
            [*[
                f"{path_name}：{round(sum(os.path.getsize(path + file) for file in os.listdir(path)) / 1024 ** 3, 2)}GB"
                if os.path.exists(path) else
                (f"{path_name}：网络路径" if is_url(path) else f"{path_name}：无效本地/网络路径")
                for path_name, path in image_path.items()
            ]]
        )
    )
    if all_info.matched or not info.matched and not storage.matched:
        await app.send_group_message(
            group, launch_time_message + "\n" + cpu_message + "\n" + memory_message + "\n" + disk_message
        )
    elif info.matched:
        await app.send_group_message(group, launch_time_message + "\n" + cpu_message + "\n" + memory_message)
    else:
        await app.send_group_message(group, launch_time_message + "\n" + disk_message)


def is_url(path: str) -> Match[str] | None:
    url_pattern = r"((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"
    json_url_pattern = r"json:([\w\W]+\.)+([\w\W]+)\$" + url_pattern
    return re.match(url_pattern, path) or re.match(json_url_pattern, path)
