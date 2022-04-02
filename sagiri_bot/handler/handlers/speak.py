import re
import json
import uuid
import base64
import asyncio
import traceback
from typing import Union
from loguru import logger
from sqlalchemy import select

from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Voice, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, WildcardMatch, RegexResult

from tencentcloud.common import credential
from tencentcloud.tts.v20190823 import tts_client, models
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl


saya = Saya.current()
channel = Channel.current()

channel.name("Speak")
channel.author("nullqwertyuiop, SAGIRI-kawaii")
channel.description("语音合成插件，在群中发送 `说 {content}` 即可")

core = AppCore.get_core_instance()
config = core.get_config()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("说"), WildcardMatch().flags(re.DOTALL) @ "content"])],
        decorators=[
            FrequencyLimit.require("speak", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def speak(app: Ariadne, message: MessageChain, group: Group, content: RegexResult):
    text = content.result.asDisplay()
    if voice := await Speak.get_voice(group.id, text):
        if isinstance(voice, str):
            await app.sendGroupMessage(group, MessageChain(voice), quote=message.getFirst(Source))
        elif isinstance(voice, bytes):
            await app.sendGroupMessage(group, MessageChain([Voice(data_bytes=await silkcoder.async_encode(voice))]))


class Speak(object):

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
                # "Codec": "wav"
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
            async with get_running(Adapter).session.get(url=url) as resp:
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
