import json
import aiohttp

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import App


async def get_song_ordered(keyword: str) -> list:
    """
    Search song from CloudMusic

    Args:
        keyword: Keyword to search

    Examples:
        message = await get_song_ordered("lemon")

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    song_search_url = "http://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s={" \
                      "%s}&type=1&offset=0&total=true&limit=1" % keyword
    # print(song_search_url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url=song_search_url) as resp:
            data_json = await resp.read()
    data_json = json.loads(data_json)

    if data_json["result"]["songCount"] == 0:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="没有搜索到呐~换一首歌试试吧！")
            ])
        ]

    song_id = data_json["result"]["songs"][0]["id"]
    detail_url = f"http://musicapi.leanapp.cn/song/detail?ids={song_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=detail_url) as resp:
            data_json = await resp.json()


    song_name = data_json["songs"][0]["name"]
    pic_url = data_json["songs"][0]["al"]["picUrl"]
    desc = data_json["songs"][0]["ar"][0]["name"]
    json_code = {
        "app": "com.tencent.structmsg",
        "desc": "音乐",
        "meta": {
            "music": {
                "action": "",
                "android_pkh_name": "",
                "app_type": 1,
                "appid": 100495085,
                "desc": desc,
                "jumpUrl": f"https://y.music.163.com/m/song/{song_id}",
                "musicUrl": f"http://music.163.com/song/media/outer/url?id={song_id}",
                "preview": pic_url,
                "sourceMsgId": 0,
                "source_icon": "",
                "source_url": "",
                "tag": "假装自己是网易云音乐的屑机器人",
                "title": song_name
            }
        },
        "prompt": f"[分享]{song_name}",
        "ver": "0.0.0.1",
        "view": "music"
    }
    return [
        "None",
        MessageChain.create([
            App(content=json.dumps(json_code))
        ])
    ]