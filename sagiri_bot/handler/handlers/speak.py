import asyncio
import base64
import json
import re
import traceback
import uuid
from typing import Union

from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Voice, Source
from graia.ariadne.message.parser.twilight import FullMatch, WildcardMatch, RegexResult
from graia.ariadne.message.parser.twilight import Twilight, SpacePolicy, ArgumentMatch, ArgResult
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graiax import silkcoder
from loguru import logger
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tts.v20190823 import tts_client, models

from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.orm.async_orm import Setting
from sagiri_bot.utils import group_setting

saya = Saya.current()
channel = Channel.current()
#
channel.name("Speak")
channel.author("nullqwertyuiop, SAGIRI-kawaii")
channel.description("语音合成插件，在群中发送 `说 {content}` 即可")

core = AppCore.get_core_instance()
config = core.get_config()

user_data = config.functions["tencent"]
cred = credential.Credential(user_data["secret_id"], user_data["secret_key"])
http_profile = HttpProfile()
http_profile.endpoint = "tts.tencentcloudapi.com"
client_profile = ClientProfile()
client_profile.httpProfile = http_profile


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([
            FullMatch("说").space(SpacePolicy.FORCE),
            ArgumentMatch("-v", "--voice", type=int, optional=True) @ "voice_type",
            WildcardMatch().flags(re.DOTALL) @ "content"])],
        decorators=[
            FrequencyLimit.require("speak", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def speak(app: Ariadne, message: MessageChain, group: Group, voice_type: ArgResult, content: RegexResult):
    text = content.result.asDisplay()
    voice_type = voice_type.result if voice_type.matched else await group_setting.get_setting(group.id, Setting.voice)
    if voice_type == "off":
        return None
    if voice := await Speak.aget_voice(text, voice_type):
        if isinstance(voice, str):
            await app.sendGroupMessage(group, MessageChain(voice), quote=message.getFirst(Source))
        elif isinstance(voice, bytes):
            await app.sendGroupMessage(
                group, MessageChain([Voice(data_bytes=await silkcoder.async_encode(voice, rate=24000))])
            )


class Speak(object):

    @staticmethod
    def get_voice(text: str, voice_type: int, is_long: bool = False) -> tuple:
        client = tts_client.TtsClient(cred, "ap-guangzhou", client_profile)
        req = models.TextToVoiceRequest() if not is_long else models.CreateTtsTaskRequest()
        params = {
            "Text": text,
            "SessionId": str(uuid.uuid4()),
            "ModelType": 1,
            "VoiceType": int(voice_type),
            "Volume": 10,
            "Codec": "wav"
        }
        req.from_json_string(json.dumps(params))
        try:
            resp = client.TextToVoice(req) if not is_long else client.CreateTtsTask(req)
        except TencentCloudSDKException as err:
            logger.error(traceback.format_exc())
            if err.get_code() == "UnsupportedOperation.TextTooLong":
                return Speak.get_voice(text, voice_type, is_long=True)
            return -1, str(err)
        if is_long:
            return 1, json.loads(resp.to_json_string())["Data"]["TaskId"]
        voice = json.loads(resp.to_json_string())["Audio"]
        return 0, base64.b64decode(voice)

    @staticmethod
    async def aget_voice(text: str, voice_type: int) -> Union[str, bytes]:
        status, data = await asyncio.get_event_loop().run_in_executor(None, Speak.get_voice, text, voice_type)
        if status != 1:
            return data
        return await Speak.aget_long_voice(data)

    @staticmethod
    def get_long_voice_status(task_id: str):
        client = tts_client.TtsClient(cred, "", client_profile)
        req = models.DescribeTtsTaskStatusRequest()
        params = {
            "TaskId": task_id
        }
        req.from_json_string(json.dumps(params))
        resp = client.DescribeTtsTaskStatus(req)
        return json.loads(resp.to_json_string())["Data"]["Status"]

    @staticmethod
    async def aget_long_voice(task_id: str):
        while True:
            status = await asyncio.get_event_loop().run_in_executor(None, Speak.get_long_voice_status, task_id)
            if status in (0, 1):
                await asyncio.sleep(1)
            elif status == 2:
                url = status["Data"]["ResultUrl"]
                break
            elif status == 3:
                return "长文本转语音失败"
        async with get_running(Adapter).session.get(url=url) as resp:
            voice = await resp.read()
        return voice
