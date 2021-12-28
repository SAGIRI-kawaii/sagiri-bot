import asyncio
import json
import uuid
import base64
import traceback
from typing import Union

import aiohttp
from loguru import logger
from graiax import silkcoder
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from graia.ariadne.event.message import Group, Member, GroupMessage

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
async def speak_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await SpeakHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class SpeakHandler(AbstractHandler):
    __name__ = "SpeakHandler"
    __description__ = "语音合成"
    __usage__ = "None"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if message.asDisplay().startswith("说 "):
            text = ''.join([plain.text for plain in message.get(Plain)])[2:].replace(" ", '，')
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            voice = await SpeakHandler.get_voice(app, group.id, text)
            if isinstance(voice, str):
                return MessageItem(MessageChain.create([Plain(text=voice)]), QuoteSource(GroupStrategy()))
            elif isinstance(voice, bytes):
                voice_element = await app.uploadVoice(await silkcoder.encode(voice))
                return MessageItem(MessageChain.create([voice_element]), Normal(GroupStrategy()))
        elif message.asDisplay().startswith("长语音查询 "):
            _, task_id = message.asDisplay().split(" ", maxsplit=1)
            if query := await SpeakHandler.get_long_voice_status(task_id):
                if query["Data"]["Status"] == 0:
                    msg = "语音正在等待合成，请稍候。"
                elif query["Data"]["Status"] == 1:
                    msg = "语音正在合成中，请稍候。"
                elif query["Data"]["Status"] == 3:
                    msg = "长文本转语音失败。"
                elif query["Data"]["Status"] == 2:
                    url = query["Data"]["ResultUrl"]
                    msg = f"语音合成成功，地址为{url}。"
                else:
                    msg = "未知状态码"
                return MessageItem(MessageChain.create([
                    Plain(text=msg)
                ]), QuoteSource(GroupStrategy()))
            return MessageItem(MessageChain.create([
                Plain(text=f"错误，请检查任务 ID 是否有效。")
            ]), QuoteSource(GroupStrategy()))

    @staticmethod
    async def get_voice(app: Ariadne, group_id: int, text: str) -> Union[str, bytes, None]:
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
                    error_code = err.get_code()
                    if error_code == "InternalError.InternalError":
                        return "内部错误，请稍后再试。"
                    elif error_code == "InvalidParameter.InvalidText":
                        return "请求文本含有非法字符，请检查您的输入。"
                    elif error_code == "InvalidParameterValue.InvalidText":
                        return "请求文本含有非法字符或不含有合法字符，请检查您的输入。"
                    elif error_code == "LimitExceeded.AccessLimit":
                        return "请求超过限制频率，请稍后再试。"
                    elif error_code == "UnsupportedOperation.AccountArrears":
                        return "账号欠费，请联系机器人管理员。"
                    elif error_code == "UnsupportedOperation.NoBanlance":
                        return "账号无余额，请联系机器人管理员。"
                    elif error_code == "UnsupportedOperation.NoFreeAccount":
                        return "账号免费额度已用完，请联系机器人管理员。"
                    elif error_code == "UnsupportedOperation.ServerNotOpen":
                        return "远端服务器未开通使用，请稍后再试。"
                    elif error_code == "UnsupportedOperation.TextTooLong":
                        return await SpeakHandler.get_long_voice(app, voice_type, text, group_id)
                    return str(err)
            else:
                return None

    @staticmethod
    async def get_long_voice(app: Ariadne, voice_type: Union[int, str], text: str, group_id: int):
        try:
            user_data = get_config("tencent")
            cred = credential.Credential(user_data["secretId"], user_data["secretKey"])
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
            await app.sendGroupMessage(group_id, MessageChain.create([
                Plain(text=f'已发送长语音合成请求，合成完毕后将自动发送，可发送 "长语音查询 任务ID" 查询合成状态。\n任务 ID：{task_id}')
            ]))
            while True:
                status = await SpeakHandler.get_long_voice_status(task_id)
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
            error_code = err.get_code()
            if error_code == "InternalError.InternalError":
                return "内部错误，请稍后再试。"
            elif error_code == "InvalidParameter.InvalidText":
                return "请求文本含有非法字符，请检查您的输入。"
            elif error_code == "InvalidParameterValue.InvalidText":
                return "请求文本含有非法字符或不含有合法字符，请检查您的输入。"
            elif error_code == "LimitExceeded.AccessLimit":
                return "请求超过限制频率，请稍后再试。"
            elif error_code == "UnsupportedOperation.AccountArrears":
                return "账号欠费，请联系机器人管理员。"
            elif error_code == "UnsupportedOperation.NoBanlance":
                return "账号无余额，请联系机器人管理员。"
            elif error_code == "UnsupportedOperation.NoFreeAccount":
                return "账号免费额度已用完，请联系机器人管理员。"
            elif error_code == "UnsupportedOperation.ServerNotOpen":
                return "远端服务器未开通使用，请稍后再试。"
            return str(err)

    @staticmethod
    async def get_long_voice_status(task_id: str):
        try:
            user_data = get_config("tencent")
            cred = credential.Credential(user_data["secretId"], user_data["secretKey"])
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
