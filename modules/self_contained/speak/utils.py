import json
import uuid
import base64
import asyncio
import aiohttp
import traceback
from typing import Union
from loguru import logger

from creart import create
from tencentcloud.common import credential
from tencentcloud.tts.v20190823 import tts_client, models
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from shared.models.config import GlobalConfig

config = create(GlobalConfig)

user_data = config.functions["tencent"]
cred = credential.Credential(str(user_data["secret_id"]), str(user_data["secret_key"]))
http_profile = HttpProfile()
http_profile.endpoint = "tts.tencentcloudapi.com"
client_profile = ClientProfile()
client_profile.httpProfile = http_profile


def get_voice(text: str, voice_type: int, is_long: bool = False) -> tuple:
    client = tts_client.TtsClient(cred, "ap-guangzhou", client_profile)
    req = (
        models.TextToVoiceRequest()
        if not is_long
        else models.CreateTtsTaskRequest()
    )
    params = {
        "Text": text,
        "SessionId": str(uuid.uuid4()),
        "ModelType": 1,
        "VoiceType": int(voice_type),
        "Volume": 10,
        "Codec": "wav",
    }
    req.from_json_string(json.dumps(params))
    try:
        resp = client.TextToVoice(req) if not is_long else client.CreateTtsTask(req)
    except TencentCloudSDKException as err:
        logger.error(traceback.format_exc())
        if err.get_code() == "UnsupportedOperation.TextTooLong":
            return get_voice(text, voice_type, is_long=True)
        return -1, str(err)
    if is_long:
        return 1, json.loads(resp.to_json_string())["Data"]["TaskId"]
    voice = json.loads(resp.to_json_string())["Audio"]
    return 0, base64.b64decode(voice)


async def aget_voice(text: str, voice_type: int) -> Union[str, bytes]:
    status, data = await asyncio.to_thread(get_voice, text, voice_type)
    if status != 1:
        return data
    return await aget_long_voice(data)


def get_long_voice_status(task_id: str):
    client = tts_client.TtsClient(cred, "", client_profile)
    req = models.DescribeTtsTaskStatusRequest()
    params = {"TaskId": task_id}
    req.from_json_string(json.dumps(params))
    resp = client.DescribeTtsTaskStatus(req)
    return json.loads(resp.to_json_string())["Data"]["Status"]


async def aget_long_voice(task_id: str):
    while True:
        status = await asyncio.to_thread(get_long_voice_status, task_id)
        if status in (0, 1):
            await asyncio.sleep(1)
        elif status == 2:
            url = status["Data"]["ResultUrl"]
            break
        elif status == 3:
            return "长文本转语音失败"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            voice = await resp.read()
    return voice
