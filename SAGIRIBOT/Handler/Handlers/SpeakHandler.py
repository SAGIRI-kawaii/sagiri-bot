import json
import uuid
import base64
import traceback
from typing import Union
from loguru import logger
from graiax import silkcoder
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.ORM.AsyncORM import orm
from SAGIRIBOT.ORM.AsyncORM import Setting, UserCalledCount
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.utils import get_config
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal, QuoteSource

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tts.v20190823 import tts_client, models


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def speak_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await SpeakHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class SpeakHandler(AbstractHandler):
    __name__ = "SpeakHandler"
    __description__ = "语音合成"
    __usage__ = "None"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("说 "):
            text = ''.join([plain.text for plain in message.get(Plain)])[2:].replace(" ", '，')
            if len(text) > 110:
                return MessageItem(MessageChain.create([Plain(text="要读的东西太长了啦！")]), QuoteSource(GroupStrategy()))
            else:
                await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
                voice = await SpeakHandler.get_voice(group.id, text)
                if isinstance(voice, str):
                    return MessageItem(MessageChain.create([Plain(text=voice)]), QuoteSource(GroupStrategy()))
                elif isinstance(voice, bytes):
                    voice_element = await app.uploadVoice(await silkcoder.encode(voice))
                    return MessageItem(MessageChain.create([voice_element]), Normal(GroupStrategy()))

    @staticmethod
    async def get_voice(group_id: int, text: str) -> Union[str, bytes]:
        if voice_type := await orm.fetchone(select(Setting.voice).where(Setting.group_id == group_id)):
            voice_type = voice_type[0]
            if voice_type != "off":
                try:
                    user_data = get_config("tencent")
                    cred = credential.Credential(user_data["secretId"], user_data["secretKey"])
                    session_ID = str(uuid.uuid4())
                    httpProfile = HttpProfile()
                    httpProfile.endpoint = "tts.tencentcloudapi.com"
                    clientProfile = ClientProfile()
                    clientProfile.httpProfile = httpProfile
                    client = tts_client.TtsClient(cred, "ap-guangzhou", clientProfile)
                    req = models.TextToVoiceRequest()
                    params = {
                        "Text": text,
                        "SessionId": session_ID,
                        "ModelType": 1,
                        "VoiceType": int(voice_type),
                        "Volume": 10,
                        "Codec": "wav"
                    }
                    req.from_json_string(json.dumps(params))
                    resp = client.TextToVoice(req)
                    voice = json.loads(resp.to_json_string())["Audio"]
                    return base64.b64decode(voice)
                except TencentCloudSDKException as err:
                    logger.error(traceback.format_exc())
                    return str(err)
            else:
                return None
