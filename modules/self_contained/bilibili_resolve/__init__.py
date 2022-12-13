import re
import json
from loguru import logger

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.element import Image, Plain, App
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult, ElementMatch, ElementResult

from .utils import get_video_info, b23_url_extract, math, info_json_dump, gen_img, url_vid_extract
from shared.utils.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl, Distribute

channel = Channel.current()
channel.name("BilibiliResolve")
channel.author("SAGIRI-kawaii")
channel.description("一个可以解析B站url/av/bv号/小程序的插件")

avid_re = r"(av|AV)(\d{1,12})"
bvid_re = "[Bb][Vv]1([0-9a-zA-Z]{2})4[1y]1[0-9a-zA-Z]7([0-9a-zA-Z]{2})"
b23_re = r"(https?://)?b23.tv/\w+"
url_re = r"(https?://)?www.bilibili.com/video/.+(\?[\w\W]+)?"
p = re.compile(f"({avid_re})|({bvid_re})")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                RegexMatch(avid_re, optional=True) @ "av",
                RegexMatch(bvid_re, optional=True) @ "bv",
                RegexMatch(b23_re, optional=True) @ "b23url",
                RegexMatch(url_re, optional=True) @ "url",
                ElementMatch(App, optional=True) @ "bapp"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("bilibili_resolve_text", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def bilibili_resolve_text(
    app: Ariadne,
    group: Group,
    message: MessageChain,
    av: RegexResult,
    bv: RegexResult,
    b23url: RegexResult,
    url: RegexResult,
    bapp: ElementResult
):
    if av.matched or bv.matched:
        vid = message.display
    elif b23url.matched or bapp.matched:
        if bapp.matched:
            bapp = bapp.result.dict()
            content = json.loads(bapp.get("content", {}))
            content = content.get("meta", {}).get("detail_1", {})
            print(content)
            if content.get("title") == "哔哩哔哩":
                b23url = content.get("qqdocurl")
            else:
                content = json.loads(bapp.get("content", {}))
                content = content.get("meta", {}).get("news", {})
                print(content)
                if "哔哩哔哩" in content.get("desc", ""):
                    b23url = content.get("jumpUrl")
                else:
                    return
        else:
            b23url = message.display
        if not (msg_str := await b23_url_extract(b23url)):
            return
        vid = p.search(msg_str).group()
    elif url.matched:
        vid = url_vid_extract(message.display)
        if not vid:
            return
    else:
        return
    video_info = await get_video_info(vid)
    if video_info['code'] == -404:
        return await app.send_message(group, MessageChain("视频不存在"))
    elif video_info['code'] != 0:
        error_text = f'解析B站视频 {vid} 时出错👇\n错误代码：{video_info["code"]}\n错误信息：{video_info["message"]}'
        logger.error(error_text)
        return await app.send_message(group, MessageChain(error_text))
    else:
        video_info = info_json_dump(video_info['data'])
        img = await gen_img(video_info)
        await app.send_group_message(
            group,
            MessageChain(
                Image(data_bytes=img),
                Plain(
                    f'\n{video_info.title}\n'
                    f'UP主：{video_info.up_name}\n'
                    f'{math(video_info.views)}播放 {math(video_info.likes)}赞\n'
                    f'链接：https://b23.tv/{video_info.bvid}'
                ),
            ),
        )
