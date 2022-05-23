import os
import psutil
import shutil 

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, ArgumentMatch, ArgResult

from sagiri_bot.control import Permission
from sagiri_bot.core.app_core import AppCore

saya = Saya.current()
channel = Channel.current()

channel.name("SystemStatus")
channel.author("SAGIRI-kawaii")
channel.description("查看系统状态")

image_path = AppCore.get_core_instance().get_config().image_path


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/sys"),
                ArgumentMatch("-i", "-info", optional=True, action="store_true") @ "info",
                ArgumentMatch("-s", "-system", optional=True, action="store_true") @ "system",
                ArgumentMatch("-d", "-disk", optional=True, action="store_true") @ "disk",
                ArgumentMatch("-b", "-battery", optional=True, action="store_true") @ "battery",
                ArgumentMatch("-m", "-menory", optional=True, action="store_true") @ "memory",
                ArgumentMatch("-c", "-cpu", optional=True, action="store_true") @ "cpu",
            ])
        ],
        decorators=[Permission.require(Permission.SUPER_ADMIN)]
    )
)
async def system_status(app: Ariadne, group: Group, system: ArgResult, info: ArgResult, disk: ArgResult, battery: ArgResult, memory: ArgResult, cpu: ArgResult):
    mem = psutil.virtual_memory()
    memory_message = MessageChain(
        "内存相关: \n"
        f"    内存总大小: {round(mem.total / (1024 ** 3), 2)}GB\n"
        f"    内存使用量: {round(mem.used / (1024 ** 3), 2)}GB ({round(mem.used / mem.total * 100, 2)}%)\n"
        f"    内存空闲量: {round(mem.free / (1024 ** 3), 2)}GB ({round(mem.free / mem.total* 100, 2)}%)"
    )
    cpu_message = MessageChain(
        "CPU相关: \n"
        f"    CPU物理核心数: {psutil.cpu_count(logical=False)}\n"
        f"    CPU总体占用: {psutil.cpu_percent()}%\n"
        f"    CPU频率: {round(psutil.cpu_freq().current / 1000, 2)}GHz"
    )
    gb = 1024 ** 3 #GB == gigabyte 
    total_b, used_b, free_b = shutil.disk_usage('/')
    total_b1, used_b1, free_b1 = shutil.disk_usage('/home')
    disk_message = MessageChain(
        "磁盘相关: \n"
        f"    /: \n" 
        f"    分区总大小: {round(total_b / gb, 2)}GB\n"
        f"    分区使用量: {round(used_b / gb, 2)}GB ({round(used_b / total_b * 100, 2)}%)\n"
        f"    分区空闲量: {round(free_b / gb, 2)}GB ({round(free_b / total_b * 100, 2)}%)\n"
        f"    /home: \n" 
        f"    分区总大小: {round(total_b1 / gb, 2)}GB\n"
        f"    分区使用量: {round(used_b1 / gb, 2)}GB ({round(used_b1 / total_b1 * 100, 2)}%)\n"
        f"    分区空闲量: {round(free_b1 / gb, 2)}GB ({round(free_b1 / total_b1 * 100, 2)}%)"
    )
    #    "    图库占用空间: \n        " +
    #    '\n        '.join([*[f"{path_name}: {round(sum([os.path.getsize(path + file) for file in os.listdir(path)]) / (1024 ** 3), 2)}GB" if os.path.exists(path) else f"{path_name}: 路径不存在" for path_name, path in image_path.items()]])
    battery_power_connected = psutil.sensors_battery().power_plugged  # 获取电脑是否连接了电
    battery_power_power = psutil.sensors_battery().percent  # 获取电池的电量
    if battery_power_connected:
        ret_power_connected = '正在充电'
    else:
        ret_power_connected = '正在放电'
    battery_message = MessageChain(
        "电池相关: \n" +
        f"    电池电量: {battery_power_power}%\n"
        f"    充电状态: {ret_power_connected}"
    )
    if info.matched or (not system.matched and not disk.matched and not memory.matched and not cpu.matched and not battery.matched):
        await app.sendGroupMessage(group, cpu_message + "\n" + memory_message + "\n" + battery_message + "\n" + disk_message)
    elif system.matched:
        await app.sendGroupMessage(group, cpu_message + "\n" + memory_message + "\n" + battery_message)
    elif disk.matched:
        await app.sendGroupMessage(group, disk_message)
    elif memory.matched:
        await app.sendGroupMessage(group, memory_message)
    elif cpu.matched:
        await app.sendGroupMessage(group, cpu_message)
    elif battery.matched:
        await app.sendGroupMessage(group, battery_message)