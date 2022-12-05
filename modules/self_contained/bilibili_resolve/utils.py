import re
import time
import qrcode
import base64
import aiohttp
from io import BytesIO
from pathlib import Path
from typing import Literal
from dataclasses import dataclass

from shared.utils.text2img import template2img

template = (Path(__file__).parent / "template.html").read_text(encoding='utf-8')


@dataclass
class VideoInfo:
    cover_url: str  # 封面地址
    bvid: str  # BV号
    avid: int  # av号
    title: str  # 视频标题
    sub_count: int  # 视频分P数
    pub_timestamp: int  # 视频发布时间（时间戳）
    unload_timestamp: int  # 视频上传时间（时间戳，不一定准确）
    desc: str  # 视频简介
    duration: int  # 视频长度（单位：秒）
    up_mid: int  # up主mid
    up_name: str  # up主名称
    views: int  # 播放量
    danmu: int  # 弹幕数
    likes: int  # 点赞数
    coins: int  # 投币数
    favorites: int  # 收藏量


@dataclass
class UserInfo:
    name: str  # 名字
    mid: int  # id
    avatar_url: str  # 头像链接
    sign: str  # 个性签名
    fans: int  # 粉丝数量
    friend: int  # 关注数量
    gender: Literal["男", "女", "保密"]  # 性别
    level: int  # 等级


async def get_video_info(vid_id: str) -> dict:
    async with aiohttp.ClientSession() as session:
        if vid_id[:2] in {"av", "aV", "Av", "AV"}:
            async with session.get(f"https://api.bilibili.com/x/web-interface/view?aid={vid_id[2:]}") as resp:
                video_info = await resp.json(content_type=resp.content_type)
        elif vid_id[:2] in {"bv", "bV", "Bv", "BV"}:
            async with session.get(f"https://api.bilibili.com/x/web-interface/view?bvid={vid_id}") as resp:
                video_info = await resp.json(content_type=resp.content_type)
        else:
            raise ValueError("视频 ID 格式错误，只可为 av 或 BV")
        return video_info


async def get_user_info(mid: int) -> UserInfo:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.bilibili.com/x/web-interface/card?mid={mid}") as resp:
            data = await resp.json(content_type=resp.content_type)
    data = data.get("data", {}).get("card")
    return UserInfo(
        mid=mid,
        name=data.get("name"),
        gender=data.get("sex"),
        avatar_url=data.get("face"),
        sign=data.get("sign"),
        level=data.get("level"),
        fans=data.get("fans"),
        friend=data.get("friend")
    )


async def b23_url_extract(b23_url: str) -> Literal[False] | str:
    url = re.search(r'b23.tv[/\\]+([0-9a-zA-Z]+)', b23_url)
    if url is None:
        return False
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://{url.group()}', allow_redirects=True) as resp:
            target = str(resp.url)
    return target if 'www.bilibili.com/video/' in target else False


def url_vid_extract(url: str) -> Literal[False] | str:
    try:
        return url.split("?")[0].split("/")[-1]
    except IndexError:
        return False


def math(num: int):
    if num < 10000:
        return str(num)
    elif num < 100000000:
        return ('%.2f' % (num / 10000)) + '万'
    else:
        return ('%.2f' % (num / 100000000)) + '亿'


def info_json_dump(obj: dict) -> VideoInfo:
    return VideoInfo(
        cover_url=obj['pic'],
        bvid=obj['bvid'],
        avid=obj['aid'],
        title=obj['title'],
        sub_count=obj['videos'],
        pub_timestamp=obj['pubdate'],
        unload_timestamp=obj['ctime'],
        desc=obj['desc'].strip(),
        duration=obj['duration'],
        up_mid=obj['owner']['mid'],
        up_name=obj['owner']['name'],
        views=obj['stat']['view'],
        danmu=obj['stat']['danmaku'],
        likes=obj['stat']['like'],
        coins=obj['stat']['coin'],
        favorites=obj['stat']['favorite'],
    )


async def gen_img(data: VideoInfo) -> bytes:
    user_info = await get_user_info(data.up_mid)
    bytes_io = BytesIO()
    qrcode_img = qrcode.make(f"https://b23.tv/{data.bvid}")
    qrcode_img.save(bytes_io)
    qrcode_base64 = base64.b64encode(bytes_io.getvalue())
    # video_length_m, video_length_s = divmod(data.duration, 60)  # 将总的秒数转换为时分秒格式
    # video_length_h, video_length_m = divmod(video_length_m, 60)
    # if video_length_h == 0:
    #     video_length = f'{video_length_m}:{video_length_s}'
    # else:
    #     video_length = f'{video_length_h}:{video_length_m}:{video_length_s}'
    return await template2img(
        template,
        {
            "bv": data.bvid,
            "av": f"av{data.avid}",
            "title": data.title,
            "desc": data.desc.strip().replace('\n', '<br/>'),
            "username": data.up_name,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.pub_timestamp)),
            "views": math(data.views),
            "likes": math(data.likes),
            "danmu": math(data.danmu),
            "coins": math(data.coins),
            "favorites": math(data.favorites),
            "cover": data.cover_url,
            "avatar": user_info.avatar_url,
            "fans": user_info.fans,
            "qrcode": f"data:image/png;base64,{qrcode_base64.decode()}"
        },
        {"viewport": {'width': 800, 'height': 10}},
    )
