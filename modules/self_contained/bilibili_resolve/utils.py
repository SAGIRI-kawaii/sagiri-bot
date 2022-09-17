import re
import time
import aiohttp
from typing import Literal
from dataclasses import dataclass

from shared.utils.text2image import md2pic


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
    video_length_m, video_length_s = divmod(data.duration, 60)  # 将总的秒数转换为时分秒格式
    video_length_h, video_length_m = divmod(video_length_m, 60)
    if video_length_h == 0:
        video_length = f'{video_length_m}:{video_length_s}'
    else:
        video_length = f'{video_length_h}:{video_length_m}:{video_length_s}'

    info_text = (
        f'BV号：{data.bvid}  \n'
        f'av号：av{data.avid}  \n'
        f'标题：{data.title}  \n'
        f'UP主：{data.up_name}  \n'
        f'时长：{video_length}  \n'
        f'发布时间：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.pub_timestamp))}  \n'
    )

    if data.sub_count > 1:
        info_text += f'分P数量：{data.sub_count}  \n'

    desc = data.desc.strip().replace('\n', '<br/>')
    info_text += (
        f'{math(data.views)}播放 {math(data.danmu)}弹幕  \n'
        f'{math(data.likes)}点赞 {math(data.coins)}投币 {math(data.favorites)}收藏\n'
        '\n---\n'
        f'### 简介\n{desc}'
    )

    return await md2pic(f'![]({data.cover_url})\n\n{info_text}')
