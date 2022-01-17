import json
import uuid
import base64
import aiohttp
import asyncio
import traceback
from typing import Union
from loguru import logger
from sqlalchemy import select

from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import UploadMethod
from graia.ariadne.message.element import Plain
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
from sagiri_bot.message_sender.strategy import Normal, QuoteSource
from sagiri_bot.message_sender.message_sender import MessageSender

from tencentcloud.common import credential
from tencentcloud.tts.v20190823 import tts_client, models
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException


saya = Saya.current()
channel = Channel.current()

channel.name("Speak")
channel.author("nullqwertyuiop, SAGIRI-kawaii")
channel.description("语音合成插件，在群中发送 `说 {content}` 即可")

core = AppCore.get_core_instance()
config = core.get_config()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def speak_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await Speak.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class Speak(AbstractHandler):
    __name__ = "Speak"
    __description__ = "语音合成插件"
    __usage__ = "在群中发送 `说 {content}` 即可"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("说 "):
            text = ''.join([plain.text for plain in message.get(Plain)])[2:].replace(" ", '，')
            await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
            if voice := await Speak.get_voice(app, group.id, text):
                if isinstance(voice, str):
                    return MessageItem(MessageChain.create([Plain(text=voice)]), QuoteSource())
                elif isinstance(voice, bytes):
                    voice_element = await app.uploadVoice(await silkcoder.encode(voice), method=UploadMethod.Group)
                    return MessageItem(MessageChain.create([voice_element]), Normal())

    @staticmethod
    async def get_voice(group_id: int, text: str) -> Union[str, bytes, None]:
        if voice_type := await orm.fetchone(select(Setting.voice).where(Setting.group_id == group_id)):
            voice_type = voice_type[0]
            if voice_type != "off":
                try:
                    user_data = config.functions["tencent"]
                    cred = credential.Credential(user_data["secret_id"], user_data["secret_key"])
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
                    if err.get_code() == "UnsupportedOperation.TextTooLong":
                        return await Speak.get_long_voice(voice_type, text)
                    return str(err)
            else:
                return None

    @staticmethod
    async def get_long_voice(voice_type: Union[int, str], text: str):
        try:
            user_data = config.functions["tencent"]
            cred = credential.Credential(user_data["secret_id"], user_data["secret_key"])
            httpProfile = HttpProfile()
            httpProfile.endpoint = "tts.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = tts_client.TtsClient(cred, "", clientProfile)
            req = models.CreateTtsTaskRequest()
            params = {
                "Text": text,
                "ModelType": 1,
                "VoiceType": int(voice_type),
                "Volume": 10,
                "Codec": "wav"
            }
            req.from_json_string(json.dumps(params))
            resp = client.CreateTtsTask(req)
            task_id = json.loads(resp.to_json_string())["Data"]["TaskId"]
            while True:
                status = await Speak.get_long_voice_status(task_id)
                if status["Data"]["Status"] in (0, 1):
                    await asyncio.sleep(1)
                elif status["Data"]["Status"] == 3:
                    return "长文本转语音失败。"
                elif status["Data"]["Status"] == 2:
                    url = status["Data"]["ResultUrl"]
                    break
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url) as resp:
                    voice = await resp.read()
                    return voice
        except TencentCloudSDKException as err:
            logger.error(traceback.format_exc())
            return str(err)

    @staticmethod
    async def get_long_voice_status(task_id: str):
        try:
            user_data = config.functions["tencent"]
            cred = credential.Credential(user_data["secret_id"], user_data["secret_key"])
            httpProfile = HttpProfile()
            httpProfile.endpoint = "tts.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = tts_client.TtsClient(cred, "", clientProfile)
            req = models.DescribeTtsTaskStatusRequest()
            params = {
                "TaskId": task_id
            }
            req.from_json_string(json.dumps(params))
            resp = client.DescribeTtsTaskStatus(req)
            return json.loads(resp.to_json_string())
        except TencentCloudSDKException:
            return None
