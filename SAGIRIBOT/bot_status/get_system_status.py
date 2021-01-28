import wmi
import platform
from pynvml import *
import datetime

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain


async def get_system_status() -> list:
    w = wmi.WMI()
    processor = w.Win32_Processor()
    m = w.Win32_ComputerSystem()
    operator = w.Win32_OperatingSystem()
    text = "     systemInfo     \n"
    text += "--------------------\n"
    text += "Platform: %s\n" % platform.platform()
    text += "--------------------\n"
    text += "CPU: \n"
    for cpu in processor: 
        text += "CPU Model: %s\n" % cpu.Name
        text += "Frequency: %sMHz\n" % cpu.CurrentClockSpeed
        text += "Number of cores: %s\n" % cpu.NumberOfCores
        text += "Usage rate: %s%%\n" % cpu.LoadPercentage
    text += "--------------------\n"
    # text += "GPU: \n"
    # for gpu in w.Win32_VideoController(): 
    #     text += "GPU Model: %s\n" % gpu.caption
    # nvmlInit()
    # handle = nvmlDeviceGetHandleByIndex(0)
    # meminfo = nvmlDeviceGetMemoryInfo(handle)
    # text += "Total memory: %2.2fG\n" % (float(meminfo.total) / 1024 / 1024 / 1024)
    # text += "Used memory: %2.2fG\n" % (float(meminfo.used) / 1024 / 1024 / 1024)
    # text += "Free memory: %2.2fG\n" % (float(meminfo.free) / 1024 / 1024 / 1024)
    # text += "--------------------\n"
    text += "Memory: \n"
    for memory in m: 
        tm = float(memory.TotalPhysicalMemory) / 1024 / 1024 / 1024
        text += "Total memory: %.2fG\n" % tm
    for os in operator: 
        text += "Used memory: %.2fG\n" % (tm - float(os.FreePhysicalMemory) / 1024 / 1024)
        text += "Free memory: %.2fG\n" % (float(os.FreePhysicalMemory) / 1024 / 1024)
    text += "--------------------\n"
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H: %M: %S")
    text += "time: %s\n" % time_now
    return [
        "None",
        MessageChain.create([
            Plain(text=text)
        ])
    ]
