import aiohttp
from yarl import URL

from creart import create

from .models import Text2Image, Image2Image
from shared.models.config import GlobalConfig

config = create(GlobalConfig)
base_url = config.functions.get("stable_diffusion_api")
headers = {"Content-Type": "application/json", "accept": "application/json"}


async def sd_req(data: Text2Image | Image2Image) -> dict:
    url = URL(base_url) / "v1" / ("txt2img" if isinstance(data, Text2Image) else "img2img")
    route = "txt2imgreq" if isinstance(data, Text2Image) else "img2imgreq"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, json={route: data.__dict__}) as resp:
            return await resp.json()
