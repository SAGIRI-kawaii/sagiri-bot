from pathlib import Path
from loguru import logger

import kayaku


def main():
    target_main_path = Path(__file__).parent.parent.parent
    if Path.cwd() != target_main_path.absolute():
        logger.critical(f"当前目录非项目所在目录！请进入{str(target_main_path.parent)}后再运行 SAGIRI-BOT!")
        exit(0)

    kayaku.initialize({
        "{**}": "./config/{**}"
    })

    from shared.service.stage import initialize

    initialize()
