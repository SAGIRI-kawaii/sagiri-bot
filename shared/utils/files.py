import yaml
import aiofiles
from pathlib import Path


async def read_file(path: str | Path) -> str:
    async with aiofiles.open(path, mode="r") as f:
        return await f.read()


async def load_yaml(path: str | Path) -> dict:
    async with aiofiles.open(path, mode="r") as f:
        return yaml.safe_load(await f.read())
