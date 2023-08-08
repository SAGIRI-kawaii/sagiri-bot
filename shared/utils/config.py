import sys
from pathlib import Path
from loguru import logger

import kayaku
from kayaku import create

from shared.models import GlobalConfig


def is_first_run() -> bool:
    cfg_path = Path("config") / "config.jsonc"
    if not cfg_path.exists():
        return True
    return cfg_path.read_bytes() == b""


def _bootstrap(msg: str) -> None:
    kayaku.bootstrap()
    kayaku.save_all()
    logger.success(msg)


def initialize_config() -> None:
    first_run = is_first_run()
    create(GlobalConfig)
    kayaku.bootstrap()
    kayaku.save_all()
    if first_run:
        _bootstrap("检测到第一次运行，请按照文档输入配置后重启机器人")
        sys.exit(1)
    _bootstrap("配置初始化完成")
