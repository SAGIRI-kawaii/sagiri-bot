import pkgutil
from pathlib import Path
from loguru import logger

from creart import create
from graia.saya import Saya

ignore = ('__init__.py', '__pycache__')


def load_modules(path: Path | str) -> None:
    saya = create(Saya)
    pre_path = str(path.relative_to(Path.cwd())).replace("/", ".")
    with saya.module_context():
        for module in pkgutil.iter_modules([str(path)]):
            if module.name in ignore or module.name[0] in ('#', '.', '_'):
                continue
            try:
                logger.info(f"正在加载模块 <{pre_path}.{module.name}>")
                saya.require(f'{pre_path}.{module.name}')
                logger.success(f"模块 <{pre_path}.{module.name}> 加载成功！")
            except Exception as e:
                logger.error(str(e))