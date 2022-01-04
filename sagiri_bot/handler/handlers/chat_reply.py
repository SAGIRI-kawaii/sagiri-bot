import json
import aiohttp
import traceback
from loguru import logger
from sqlalchemy import select
from tencentcloud.common import credential
from tencentcloud.nlp.v20190408 import nlp_client, models
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain, At
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.utils import update_user_call_count_plus
from sagiri_bot.orm.async_orm import Setting, UserCalledCount
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import AtSender, DoNothing


saya = Saya.current()
channel = Channel.current()

channel.name("ChatReply")
channel.author("SAGIRI-kawaii")
channel.description("一个可以实现智能回复的插件，在群中发送 `@bot + 想说的话` 即可")

config = AppCore.get_core_instance().get_config()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def chat_reply(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await ChatReply.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class ChatReply(AbstractHandler):
    __name__ = "ChatReply"
    __description__ = "一个可以实现智能回复的插件"
    __usage__ = "在群中发送 `@bot + 想说的话` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.has(At) and message.get(At)[0].target == config.bot_qq:
            await update_user_call_count_plus(group, member, UserCalledCount.at, "at")
            content = "".join(plain.text for plain in message.get(Plain)).strip().replace(" ", "，")
            return await ChatReply.get_reply(group.id, content)
        else:
            return None

    @staticmethod
    async def get_reply(group_id: int, content: str):
        if mode_now := await orm.fetchone(select(Setting.speak_mode).where(Setting.group_id == group_id)):
            mode_now = mode_now[0]
            if mode_now == "normal":
                return None
            elif mode_now == "zuanLow":
                url = f"https://nmsl.shadiao.app/api.php?level=min&from={config.functions['shadiao_app_name']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url) as resp:
                        text = await resp.text()
            elif mode_now == "zuanHigh":
                url = f"https://nmsl.shadiao.app/api.php?from={config.functions['shadiao_app_name']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url) as resp:
                        text = await resp.text()
            elif mode_now == "rainbow":
                url = f"https://chp.shadiao.app/api.php?from={config.functions['shadiao_app_name']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url) as resp:
                        text = await resp.text()

            elif mode_now == "chat":
                user_data = config.functions['tencent']
                if user_data["secret_id"] == "secret_id" or user_data["secret_key"] == "secret_key":
                    return MessageItem(MessageChain.create([Plain(text="secret_id/secret_key未初始化")]), DoNothing())
                text = await ChatReply.get_chat_reply(content)
            else:
                raise Exception(f"数据库群 <{group_id}> speak_mode项非法！目前值：{mode_now}")
            return MessageItem(MessageChain.create([Plain(text=f" {text}")]), AtSender())
        else:
            raise Exception(f"数据库未查找到群 <{group_id}> speak_mode项，请检查数据库！")

    @staticmethod
    async def get_chat_reply(query: str) -> str:
        try:
            user_data = config.functions['tencent']
            cred = credential.Credential(user_data["secret_id"], user_data["secret_key"])
            httpProfile = HttpProfile()
            httpProfile.endpoint = "nlp.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = nlp_client.NlpClient(cred, "ap-guangzhou", clientProfile)

            req = models.ChatBotRequest()
            params = {"Query": query}
            req.from_json_string(json.dumps(params))
            resp = client.ChatBot(req)
            reply = json.loads(resp.to_json_string())["Reply"].replace("腾讯小龙女", "纱雾酱").replace("小龙女", "纱雾酱")
            return reply
        except TencentCloudSDKException as e:
            logger.error(traceback.format_exc())
            return str(e)
