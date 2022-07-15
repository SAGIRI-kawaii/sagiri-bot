import json
import re
import time
from typing import Optional

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, WildcardMatch
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from sagiri_bot.control import (
    FrequencyLimit,
    BlackListControl,
    Function,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("BilibiliLinkResolve")
channel.author("nullqwertyuiop")
channel.description("B站链接解析")

CUSTOMIZATION = "%封面%\n【标题】%标题%\n【UP主】%up%\n【播放量】%播放量%\n【点赞量】%点赞量%\n【简介】%简介%"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    WildcardMatch(),
                    RegexMatch(
                        r"(http:|https:\/\/)?([^.]+\.)?"
                        r"(bilibili\.com\/video\/"
                        r"((BV|bv)[\w\d]{10}|"
                        r"((AV|av)([\d]+))))|"
                        r"(b23\.tv\/[\w\d]+)"
                    ).flags(re.S),
                    WildcardMatch(),
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("bilibili_link_resolve", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def bilibili_link_resolve_handler(app: Ariadne, event: MessageEvent):
    if msg := await BilibiliLinkResolve.resolve(event.messageChain.asDisplay()):
        await app.sendMessage(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            msg,
        )


class BilibiliLinkResolve:
    @classmethod
    async def resolve(cls, message: str) -> Optional[MessageChain]:
        if match := re.findall(
            r"(?:https?://)?(?:[^.]+\.)?bilibili\.com/video/(?:BV|bv)(\w{10})",
            message,
        ):
            bv = f"bv{match[0]}"
            av = cls.bv_to_av(bv)
            info = await BilibiliLinkResolve.get_info(av)
            return await cls.generate_messagechain(info)
        elif match := re.findall(
            r"(?:https?://)?(?:[^.]+\.)?bilibili\.com/video/(?:AV|av)(\d+)",
            message,
        ):
            av = match[0]
            info = await cls.get_info(av)
            return await cls.generate_messagechain(info)
        elif match := re.findall(r"(https?://\)?(?:[^.]+\.)?b23\.tv/\w+)", message):
            match = match[0]
            if not (match.startswith("http")):
                match = f"https://{match}"
            async with aiohttp.ClientSession() as session:
                async with session.get(match) as res:
                    if res.status == 200:
                        link = str(res.url)
                        return await cls.resolve(link)

    @staticmethod
    async def get_info(av: int):
        bilibili_video_api_url = (
            f"https://api.bilibili.com/x/web-interface/view?aid={av}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url=bilibili_video_api_url) as resp:
                result = (await resp.read()).decode("utf-8")
        result = json.loads(result)
        return result

    @staticmethod
    def bv_to_av(bv: str) -> int:
        table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
        tr = {table[i]: i for i in range(58)}
        s = [11, 10, 3, 8, 4, 6]
        xor = 177451812
        add = 8728348608
        r = sum(tr[bv[s[i]]] * 58**i for i in range(6))
        return (r - add) ^ xor

    @classmethod
    async def generate_messagechain(cls, info: dict) -> MessageChain:
        data = info["data"]
        chain_list = []
        try:
            if "%封面%" in CUSTOMIZATION:
                first = bool(CUSTOMIZATION.startswith("%封面%"))
                parsed_config = CUSTOMIZATION.split("%封面%")
                img_url = data["pic"]
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=img_url) as resp:
                        img_content = await resp.read()
                cover = Image(data_bytes=img_content)
                chain_list.append(cover if first else Plain(""))
                chain_list.extend(
                    Plain(text=cls.replace_variable(item, data))
                    for item in parsed_config
                )
            else:
                chain_list = [Plain(text=cls.replace_variable(CUSTOMIZATION, data))]
        except Exception as e:
            return MessageChain(f"解析失败，请联系机器人管理员。\n{e}")
        return MessageChain(chain_list)

    @classmethod
    def replace_variable(cls, text: str, data: dict) -> str:
        try:
            description = str(data["desc"]).replace("\\n", "\n")
            if len(description) >= 200:
                description = f"{description[:200]}..."
            text = text.replace("%标题%", str(data["title"]))
            text = text.replace(
                "%分区%",
                str(data["tid"]),
            )
            text = text.replace("%视频类型%", "原创" if data["copyright"] == 1 else "转载")
            text = text.replace(
                "%投稿时间%",
                str(time.strftime("%Y-%m-%d", time.localtime(int(data["pubdate"])))),
            )
            text = text.replace("%视频长度%", str(cls.sec_format(data["duration"])))
            text = text.replace("%up%", str(data["owner"].get("name", "")))
            text = text.replace("%播放量%", str(data["stat"].get("view", "")))
            text = text.replace("%弹幕量%", str(data["stat"].get("danmaku", "")))
            text = text.replace("%评论量%", str(data["stat"].get("reply", "")))
            text = text.replace("%点赞量%", str(data["stat"].get("like", "")))
            text = text.replace("%投币量%", str(data["stat"].get("coin", "")))
            text = text.replace("%收藏量%", str(data["stat"].get("favorite", "")))
            text = text.replace("%转发量%", str(data["stat"].get("share", "")))
            text = text.replace("%简介%", description)
            text = text.replace("%av号%", "av" + str(data["aid"]))
            text = text.replace("%bv号%", str(data["bvid"]))
            text = text.replace(
                "%链接%", f"https://www.bilibili.com/video/av{str(data['aid'])}"
            )
        except Exception as err:
            logger.error(err)
        finally:
            return text

    @staticmethod
    def sec_format(secs: int) -> str:
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return "%2d:%2d:%2d" % (h, m, s)
