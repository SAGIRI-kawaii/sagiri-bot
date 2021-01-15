import os

from SAGIRIBOT.basics.get_config import get_config


async def get_file_count(base_name: str) -> int:
    base_path = {
        "setu": await get_config("setuPath"),
        "setu18": await get_config("setu18Path"),
        "real": await get_config("realPath"),
        "realHighq": await get_config("realHighqPath"),
        "bizhi": await get_config("wallpaperPath")
    }
    if base_name in base_path.keys():
        return len(os.listdir(base_path[base_name]))
    else:
        raise Exception("get_file_count: 程序内部错误！无此路径！")
