import os
import random


async def random_pic(base_path: str) -> str:
    """
    Return random pic path in base_dir

    Args:
        base_path: Target library path

    Examples:
        pic_path = random_pic(wallpaper_path)

    Return:
        str: Target pic path
    """
    path_dir = os.listdir(base_path)
    path = random.sample(path_dir, 1)[0]
    return base_path + path
