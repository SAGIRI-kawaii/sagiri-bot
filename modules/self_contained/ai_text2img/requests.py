import json

import aiohttp
from yarl import URL
from typing import Literal

from creart import create

from .models import Text2Image, Image2Image
from shared.models.config import GlobalConfig

config = create(GlobalConfig)
base_url = config.functions.get("stable_diffusion_api")
headers = {"Content-Type": "application/json", "accept": "application/json"}


async def req(url: URL, method: Literal["GET", "POST"], **kwargs) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, **kwargs) as resp:
            return await resp.json()


async def get_models() -> list[str]:
    url = URL(base_url) / "sdapi" / "v1" / "sd-models"
    return [i["title"] for i in (await req(url, "GET"))]


async def change_model(name: str) -> dict:
    url = URL(base_url) / "sdapi" / "v1" / "load_model"
    return await req(url, "POST", data=json.dumps({"model_name": name.strip()}))


async def sd_req(data: Text2Image | Image2Image) -> dict:
    url = URL(base_url) / "sdapi" / "v1" / ("txt2img" if isinstance(data, Text2Image) else "img2img")
    return await req(url, "POST", json=data.__dict__)


async def get_status() -> dict:
    url = URL(base_url) / "sdapi" / "v1" / "memory"
    return await req(url, "GET")
