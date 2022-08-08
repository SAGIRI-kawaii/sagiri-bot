import json
import aiohttp
import traceback

from loguru import logger
from graia.saya import Saya, Channel

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain, At
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, ElementMatch, WildcardMatch, ElementResult
from graia.saya.builtins.broadcast.schema import ListenerSchema

from tencentcloud.common import credential
from tencentcloud.nlp.v20190408 import nlp_client, models
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from sagiri_bot.config import GlobalConfig
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.internal_utils import group_setting
from sagiri_bot.control import Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("ChatReply")
channel.author("SAGIRI-kawaii")
channel.description("一个可以实现智能回复的插件，在群中发送 `@bot + 想说的话` 即可")

config = create(GlobalConfig)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At) @ "at",
                    WildcardMatch()
                ]
            )
        ],
        decorators=[
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.AT)
        ]
    )
)
async def chat_reply(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    member: Member,
    at: ElementResult
):
    assert isinstance(at.result, At)
    if at.result.target == config.bot_qq:
        content = "".join(plain.text for plain in message.get(Plain)).strip().replace(" ", "，")
        mode_now = await group_setting.get_setting(group, Setting.speak_mode)

        if mode_now in ("normal", "zuanLow", "zuanLow"):
            return

        elif mode_now == "rainbow":
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.shadiao.app/chp") as resp:
                    text = (await resp.json())['data']['text']

        elif mode_now == "chat":
            user_data = config.functions['tencent']
            if user_data["secret_id"] == "secret_id" or user_data["secret_key"] == "secret_key":
                text = "secret_id/secret_key未初始化"
            else:
                try:
                    user_data = config.functions['tencent']
                    cred = credential.Credential(user_data["secret_id"], user_data["secret_key"])
                    http_profile = HttpProfile()
                    http_profile.endpoint = "nlp.tencentcloudapi.com"

                    client_profile = ClientProfile()
                    client_profile.httpProfile = http_profile
                    client = nlp_client.NlpClient(cred, "ap-guangzhou", client_profile)

                    req = models.ChatBotRequest()
                    params = {"Query": content}
                    req.from_json_string(json.dumps(params))
                    resp = client.ChatBot(req)
                    text = json.loads(resp.to_json_string())["Reply"]\
                        .replace("腾讯小龙女", "纱雾酱").replace("小龙女", "纱雾酱").replace("姑姑", "纱雾酱")
                except TencentCloudSDKException as e:
                    logger.error(traceback.format_exc())
                    text = str(e)

        else:
            raise Exception(f"数据库群 <{group.id}> speak_mode项非法！目前值：{mode_now}")

        if text:
            await app.send_group_message(group, MessageChain([
                At(target=member.id),
                Plain(text=f" {text}")
            ]))
