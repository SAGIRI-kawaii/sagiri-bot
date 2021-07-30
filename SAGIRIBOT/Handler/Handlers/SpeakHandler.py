import time
import random
import string
import base64
import aiohttp
from typing import Union
from graiax import silkcoder

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.utils import get_config, get_tx_sign
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal, QuoteSource

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
            voice = await SpeakHandler.get_voice(text)
            if isinstance(voice, str):
                return MessageItem(MessageChain.create([Plain(text=voice)]), QuoteSource(GroupStrategy()))
            elif isinstance(voice, bytes):
                voice_element = await app.uploadVoice(await silkcoder.encode(voice))
                return MessageItem(MessageChain.create([voice_element]), Normal(GroupStrategy()))

    @staticmethod
    async def get_voice(text: str) -> Union[str, bytes]:
        url = "https://api.ai.qq.com/fcgi-bin/aai/aai_tts"
        text = text.strip()
        app_id = get_config("txAppId")
        t = time.time()
        time_stamp = str(int(t))
        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 10))

        params = {
            'app_id': app_id,
            'time_stamp': time_stamp,
            'nonce_str': nonce_str,
            "speaker": '7',
            "format": '3',
            "volume": '0',
            "speed": "100",
            "text": text,
            "aht": '0',
            "apc": "58"
        }
        sign = await get_tx_sign(params)
        params["sign"] = sign
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params) as resp:
                res = await resp.json()
        if res["ret"] > 0:
            print(res)
            return f"Error:{res['msg']}"
        return base64.b64decode(res["data"]["speech"])
