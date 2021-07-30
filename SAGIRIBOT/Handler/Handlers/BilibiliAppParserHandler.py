import json
import time
import aiohttp

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, Member, GroupMessage
from graia.application.message.elements.internal import App, Plain, Image

from SAGIRIBOT.utils import sec_format
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.static_datas import bilibili_partition_dict
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def bilibili_app_parser_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await BilibiliAppParserHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class BilibiliAppParserHandler(AbstractHandler):
    __name__ = "BilibiliAppParserHandler"
    __description__ = "一个可以解析BiliBili小程序的Handler"
    __usage__ = "当群中有人分享时自动触发"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if apps := message.get(App):
            app_json = json.loads(apps[0].content)
            if app_json["prompt"] == "[QQ小程序]哔哩哔哩" or "meta" in app_json and "detail_1" in app_json["meta"] and app_json["meta"]["detail_1"]["title"] == "哔哩哔哩":
                short_url = app_json["meta"]["detail_1"]["qqdocurl"]

                async with aiohttp.ClientSession() as session:
                    async with session.get(url=short_url, allow_redirects=False) as resp:
                        result = (await resp.read()).decode("utf-8")
                bv_url = result.split("\"")[1].split("?")[0].split("/")[-1].strip()
                # print(bv_url)

                bilibili_video_api_url = f"http://api.bilibili.com/x/web-interface/view?aid={BilibiliAppParserHandler.bv_to_av(bv_url)}"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url=bilibili_video_api_url) as resp:
                        result = (await resp.read()).decode('utf-8')
                result = json.loads(result)
                return MessageItem(await BilibiliAppParserHandler.generate_messagechain(result), Normal(GroupStrategy()))

            else:
                return None
        else:
            return None

    @staticmethod
    def bv_to_av(bv: str) -> int:
        table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
        tr = {}
        for i in range(58):
            tr[table[i]] = i
        s = [11, 10, 3, 8, 4, 6]
        xor = 177451812
        add = 8728348608
        r = 0
        for i in range(6):
            r += tr[bv[s[i]]] * 58 ** i
        return (r - add) ^ xor

    @staticmethod
    def av_to_bv(av: int) -> str:
        table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
        tr = {}
        for i in range(58):
            tr[table[i]] = i
        s = [11, 10, 3, 8, 4, 6]
        xor = 177451812
        add = 8728348608
        av = (av ^ xor) + add
        r = list('BV1  4 1 7  ')
        for i in range(6):
            r[s[i]] = table[av // 58 ** i % 58]
        return ''.join(r)

    @staticmethod
    async def generate_messagechain(info: dict) -> MessageChain:
        data = info["data"]
        chain_list = []

        chain_list.append(Plain(text=f"【标题】{data['title']}\n"))

        img_url = data['pic']
        async with aiohttp.ClientSession() as session:
            async with session.get(url=img_url) as resp:
                img_content = await resp.read()

        chain_list.append(Image.fromUnsafeBytes(img_content))
        chain_list.append(Plain(text=f"\n【分区】{bilibili_partition_dict[str(data['tid'])]['name']}->{data['tname']}\n"))
        chain_list.append(Plain(text=f"【视频类型】{'原创' if data['copyright'] == 1 else '转载'}\n"))
        chain_list.append(Plain(text=f"【投稿时间】{time.strftime('%Y-%m-%d', time.localtime(int(data['pubdate'])))}\n"))
        chain_list.append(Plain(text=f"【视频长度】{sec_format(data['duration'])}\n"))
        chain_list.append(Plain(text=f"【UP主】\n    【名字】{data['owner']['name']}\n    【UID】：{data['owner']['mid']}\n"))
        if "staff" in data:
            char = "\n"
            chain_list.append(Plain(text=f"""【合作成员】\n{char.join([f"【{staff['title']}】{staff['name']}" for staff in data['staff']])}\n"""))
        chain_list.append(Plain(text="【视频数据】\n"))
        chain_list.append(Plain(text=f"    【播放量】{data['stat']['view']}\n"))
        chain_list.append(Plain(text=f"    【弹幕量】{data['stat']['danmaku']}\n"))
        chain_list.append(Plain(text=f"    【评论量】{data['stat']['reply']}\n"))
        chain_list.append(Plain(text=f"    【点赞量】{data['stat']['like']}\n"))
        chain_list.append(Plain(text=f"    【投币量】{data['stat']['coin']}\n"))
        chain_list.append(Plain(text=f"    【收藏量】{data['stat']['favorite']}\n"))
        chain_list.append(Plain(text=f"    【转发量】{data['stat']['share']}\n"))
        chara, charb = "\\n", "\n"
        chain_list.append(Plain(text=f"【简介】{data['desc'].replace(chara, charb)}\n"))
        chain_list.append(Plain(text=f"【AV】av{data['aid']}\n"))
        chain_list.append(Plain(text=f"【BV】{data['bvid']}\n"))
        chain_list.append(Plain(text=f"【链接】https://www.bilibili.com/video/av{data['aid']}"))
        return MessageChain.create(chain_list)
        # return await MessageChainUtils.messagechain_to_img(MessageChain.create(chain_list))
