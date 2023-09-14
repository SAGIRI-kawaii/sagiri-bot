import aiohttp
from PIL import Image
from io import BytesIO
from pathlib import Path
from typing import Literal
from dataclasses import dataclass, field

from shared.utils.text2img import template2img

EngineType = Literal["wyy", "qq"]


@dataclass
class Song:
    title: str
    artists: str
    album: str
    jump_url: str
    music_url: str
    alias: list[str] = field(default_factory=license)
    picture_url: str = "https://p2.music.126.net/6y-UleORITEDbvrOLV0Q8A==/5639395138885805.jpg"
    content: bytes | None = None
    engine: EngineType = "wyy"

    @staticmethod
    async def get_bytes(url: str, **kwargs) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, **kwargs) as resp:
                return await resp.read()

    async def get_cover(self) -> bytes:
        return await self.get_bytes(self.picture_url)
    
    async def get_song(self) -> bytes:
        return await self.get_bytes(
            self.music_url, 
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/104.0.0.0 Safari/537.36"
            }
        )


async def get_wyy_song(keyword: str) -> Song | None:
    url = f"https://netease-cloud-music-api-blue-kappa.vercel.app/search?keywords={keyword}" \
          f"&type=1&offset=0&total=true&limit=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json(content_type=resp.content_type)
    if data := data.get("result"):
        if not data.get("songCount", 0):
            return None
        data = data.get("songs", [])[0]
        music_id = data.get("id", -1)
        music_name = data.get("name", "null")
        artists = "、".join(i["name"] for i in data.get("artists", []))
        album = data.get("album", {}).get("name")
        alias = data.get("alias", [])
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://autumnfish.cn/song/detail?ids={music_id}",
                headers={
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/104.0.0.0 Safari/537.36"
                }
            ) as resp:
                picture_url = (await resp.json(content_type=resp.content_type)).get("songs", [{}])[0].get("al", {}).get(
                    "picUrl", "https://p2.music.126.net/6y-UleORITEDbvrOLV0Q8A==/5639395138885805.jpg"
                )
        return Song(
            title=music_name,
            album=album,
            jump_url=f"https://y.music.163.com/m/song/{music_id}/",
            picture_url=picture_url,
            artists=artists,
            alias=alias,
            music_url=f"https://music.163.com/song/media/outer/url?id={music_id}"
        )


async def get_dominant_colors(song: Song, size: int = 10) -> list[tuple]:
    image = Image.open(BytesIO(await song.get_cover()))
    result = image.convert("P", palette=Image.ADAPTIVE, colors=size)

    palette = result.getpalette()
    color_counts = sorted(result.getcolors(), reverse=True)
    colors = []

    for i in range(size):
        palette_index = color_counts[i][1]
        dominant_color = palette[palette_index * 3: palette_index * 3 + 3]
        colors.append(tuple(dominant_color))

    return colors


async def gen_desc_image(song: Song, size: int = 10) -> bytes:
    colors = await get_dominant_colors(song, size)
    return await template2img(
        (Path(__file__).parent / "template.html").read_text(),
        {
            "background": f"rgb{colors[0]}",
            "colors": ",".join([
                f"radial-gradient(closest-side, rgba({i[0]}, {i[1]}, {i[2]}, 1), rgba({i[0]}, {i[1]}, {i[2]}, 0))" 
                for i in colors[1:]
            ]),
            "cover": song.picture_url,
            "title": song.title,
            "author": song.artists,
            "album": song.album,
            "alias": song.alias[:3]
        }
    )
