import os
import psutil

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, ArgumentMatch, ArgResult

from sagiri_bot.control import Permission
from sagiri_bot.config import GlobalConfig

saya = Saya.current()
channel = Channel.current()

channel.name("SystemStatus")
channel.author("SAGIRI-kawaii")
channel.description("查看系统状态")

image_path = create(GlobalConfig).image_path


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("/sys"),
                    ArgumentMatch("-a", "-all", optional=True, action="store_true")
                    @ "all_info",
                    ArgumentMatch("-i", "-info", optional=True, action="store_true")
                    @ "info",
                    ArgumentMatch("-s", "-storage", optional=True, action="store_true")
                    @ "storage",
                ]
            )
        ],
        decorators=[Permission.require(Permission.SUPER_ADMIN)],
    )
)
async def system_status(
    app: Ariadne, group: Group, all_info: ArgResult, info: ArgResult, storage: ArgResult
):
    mem = psutil.virtual_memory()
    memory_message = MessageChain(
        "内存相关：\n"
        f"    内存总大小：{round(mem.total / (1024 ** 3), 2)}GB\n"
        f"    内存使用量：{round(mem.used / (1024 ** 3), 2)}GB / "
        f"{round(mem.total / (1024 ** 3), 2)}GB ({round(mem.used / mem.total * 100, 2)}%)\n"
        f"    内存空闲量：{round(mem.free / (1024 ** 3), 2)}GB / "
        f"{round(mem.total / (1024 ** 3), 2)}GB ({round(mem.free / mem.total* 100, 2)}%)"
    )
    cpu_message = MessageChain(
        "CPU相关：\n"
        f"    CPU 物理核心数：{psutil.cpu_count(logical=False)}\n"
        f"    CPU总体占用：{psutil.cpu_percent()}%\n"
        f"    CPU频率：{psutil.cpu_freq().current}MHz"
    )
    disk_message = MessageChain(
        (
            "磁盘相关：\n"
            + "    图库占用空间：\n        "
            + "\n        ".join(
                [
                    *[
                        f"{path_name}：{round(sum(os.path.getsize(path + file) for file in os.listdir(path)) / 1024 ** 3, 2)}GB"
                        if os.path.exists(path)
                        else f"{path_name}：路径不存在"
                        for path_name, path in image_path.items()
                    ]
                ]
            )
        )
    )

    if all_info.matched or (not info.matched and not storage.matched):
        await app.send_group_message(
            group, cpu_message + "\n" + memory_message + "\n" + disk_message
        )
    elif info.matched:
        await app.send_group_message(group, cpu_message + "\n" + memory_message)
    else:
        await app.send_group_message(group, disk_message)
