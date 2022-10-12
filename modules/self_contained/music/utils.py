import aiohttp
from typing import Literal, Tuple

from graiax.silkcoder import async_encode
from graia.ariadne.message.element import Voice, MusicShare, MusicShareKind


async def wyy_handle(
    keyword: str, send_type: Literal["voice", "card", "file"]
) -> Voice | MusicShare | Tuple[str, bytes] | None:
    url = f"https://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s={keyword}" \
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
        summary = f"{artists} - {album}" if album else artists
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
        if send_type == "card":
            return MusicShare(
                kind=MusicShareKind.NeteaseCloudMusic,
                title=music_name,
                summary=summary,
                jumpUrl=f"https://y.music.163.com/m/song/{music_id}/",
                pictureUrl=picture_url,
                musicUrl=f"https://music.163.com/song/media/outer/url?id={music_id}",
                brief=f"[分享] {music_name}"
            )
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://music.163.com/song/media/outer/url?id={music_id}",
                headers={
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/104.0.0.0 Safari/537.36"
                }
            ) as resp:
                data = await resp.read()
        return Voice(data_bytes=await async_encode(data)) if send_type == "voice" else (music_name, data)


async def qq_handle(
    keyword: str, send_type: Literal["voice", "card", "file"]
) -> Voice | MusicShare | Tuple[str, bytes] | None: ...


handlers = {
    "qq": None,
    "wyy": wyy_handle
}
