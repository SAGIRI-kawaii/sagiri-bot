from PIL import Image as IMG
from urllib import parse
from io import BytesIO
import aiohttp
import hashlib
import base64
import random
import string
import time
import io
import os

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import At

from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.data_manage.update_data.set_get_image_ready import set_get_img_ready
from SAGIRIBOT.data_manage.update_data.update_total_calls import update_total_calls
from SAGIRIBOT.data_manage.get_data.get_total_calls import get_total_calls
from SAGIRIBOT.basics.tools import get_tx_sign
from SAGIRIBOT.basics.tools import img_to_base_64


async def image_yellow_judge(group_id: int, sender: int, img: Image, usage_occasion: str) -> list:
    """
    Return the yellow judge score from Tencent Ai Platform

    Args:
        group_id: Group id
        sender: Sender
        img: Image to judge(Graia.Image)
        usage_occasion: Which function use this function

    Examples:
        message = await image_yellow_judge(group_id, sender, image, "yellowPredict")

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    await set_get_img_ready(group_id, sender, False, "yellowPredictReady")
    yellow_predict_count = await get_total_calls("search") + 1
    await update_total_calls(yellow_predict_count, "search")
    if usage_occasion == "yellowPredict":
        path = "%s%s.png" % (await get_config("yellowJudgePath"), yellow_predict_count)
    elif usage_occasion == "tribute":
        path = "%s%s.png" % (await get_config("tributePath"), yellow_predict_count)
    else:
        path = "temp//"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=img.url) as resp:
            img_content = await resp.read()

    image = IMG.open(BytesIO(img_content))
    image.save(path)
    img_base64 = await img_to_base_64(path)
    url = "https://api.ai.qq.com/fcgi-bin/vision/vision_porn"
    # 请求时间戳（秒级），用于防止请求重放（保证签名5分钟有效)
    t = time.time()
    time_stamp = str(int(t))
    # 请求随机字符串，用于保证签名不可预测  
    nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 10))
    # 应用标志，这里修改成自己的id和key
    app_id = await get_config("txAppId")
    params = {
        'app_id': app_id,
        'time_stamp': time_stamp,
        'nonce_str': nonce_str,
        'image': img_base64
    }
    params['sign'] = await get_tx_sign(params)

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, data=params) as resp:
            res = await resp.json()

    if res["ret"] > 0:
        # record("yellowJudge",path,sender,groupId,0,"img")
        return [
            "None",
            MessageChain.create([
                At(target=sender),
                Plain("Error!:\nReason:"),
                Plain(text="%s" % res["msg"])
            ])
        ]
    elif res["ret"] == 0:
        # record("yellowJudge",dist,sender,groupId,1,"img")
        return [
            "quoteSource",
            MessageChain.create([
                At(target=sender),
                Plain("\nPossible Result:\n"),
                Plain("Normal :%d%%\n" % res["data"]["tag_list"][0]["tag_confidence"]),
                Plain("Hot :%d%%\n" % res["data"]["tag_list"][1]["tag_confidence"]),
                Plain("Sexy :%d%%\n" % res["data"]["tag_list"][2]["tag_confidence"]),
                Plain("Total :%d%%" % res["data"]["tag_list"][9]["tag_confidence"])
            ])
        ]
