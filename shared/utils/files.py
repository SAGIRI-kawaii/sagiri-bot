import yaml
import json
import aiofiles
from pathlib import Path


async def read_file(path: str | Path) -> str:
    async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
        return await f.read()


async def load_yaml(path: str | Path) -> dict:
    async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
        return yaml.safe_load(await f.read())


def load_json(path: str | Path) -> dict:
    with open(path, mode="r", encoding="utf-8") as r:
        return json.load(r)
