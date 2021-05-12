import re
import os
import aiohttp
from io import BytesIO
from PIL import Image as IMG

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.ORM.AsyncORM import Setting, UserCalledCount
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.utils import get_config, get_setting, update_user_call_count_plus1

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def abbreviated_prediction_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await LoliconKeywordSearchHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class LoliconKeywordSearchHandler(AbstractHandler):
    __name__ = "LoliconKeywordSearchHandler"
    __description__ = "一个接入loliconapi的Handler"
    __usage__ = "在群中发送 `来点xx[色涩瑟]图`"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r"来点.+[色涩瑟]图", message.asDisplay()):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            await update_user_call_count_plus1(group, member, UserCalledCount.setu, "setu")
            keyword = re.findall(r"来点(.*?)[色涩瑟]图", message.asDisplay(), re.S)[0]
            return await LoliconKeywordSearchHandler.get_image(group, member, keyword)
        else:
            return None

    @staticmethod
    @frequency_limit_require_weight_free(2)
    async def get_image(group: Group, member: Member, keyword: str):
        apikey = get_config("loliconApiKey")
        if not apikey or apikey == "loliconApiKey":
            return MessageItem(MessageChain.create([Plain(text="loliconApiKey配置错误！")]), Normal(GroupStrategy()))
        cache = get_config("loliconImageCache")
        r18 = await get_setting(group.id, Setting.r18)
        url = f"https://api.lolicon.app/setu/?r18=0&keyword={keyword}&apikey={apikey}&r18={1 if r18 else 0}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                result = await resp.json()
        if result["code"] == 401:
            return MessageItem(MessageChain.create([Plain(text="错误401：APIKEY 不存在或被封禁!")]), Normal(GroupStrategy()))
        elif result["code"] == 403:
            return MessageItem(MessageChain.create([Plain(text="错误403：由于不规范的操作而被拒绝调用！")]), Normal(GroupStrategy()))
        elif result["code"] == 404:
            return MessageItem(MessageChain.create([Plain(text="错误404：找不到符合关键字的色图！")]), Normal(GroupStrategy()))
        elif result["code"] == 429:
            return MessageItem(MessageChain.create([Plain(text="错误429：达到调用额度限制！")]), Normal(GroupStrategy()))
        elif result["code"] == -1:
            return MessageItem(MessageChain.create([Plain(text="错误-1：API内部错误，请向 i@loli.best 反馈！")]), Normal(GroupStrategy()))
        result = result["data"][0]
        info = f"title: {result['title']}\nauthor: {result['author']}\nurl: {result['url']}"
        file_name = result["url"].split('/').pop()
        local_path = get_config("setu18Path" if r18 else "setuPath")
        file_path = os.path.join(local_path, file_name)
        if os.path.exists(file_path):
            return MessageItem(
                MessageChain.create([
                    Plain(text=f"你要的{keyword}涩图来辣！\n"),
                    Image.fromLocalFile(file_path),
                    Plain(text=f"\n{info}")
                ]),
                Normal(GroupStrategy())
            )
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=result['url']) as resp:
                    img_content = await resp.read()
            if cache:
                image = IMG.open(BytesIO(img_content))
                image.save(file_path)
            return MessageItem(
                MessageChain.create([
                    Plain(text=f"你要的{keyword}涩图来辣！\n"),
                    Image.fromUnsafeBytes(img_content),
                    Plain(text=f"\n{info}")
                ]),
                Normal(GroupStrategy())
            )
