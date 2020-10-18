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

from functions.basics.get_config import get_config
from functions.data_manage.update_data.set_get_image_ready import set_get_img_ready
from functions.data_manage.update_data.update_total_calls import update_total_calls
from functions.data_manage.get_data.get_total_calls import get_total_calls


async def base_64(pic_path: str) -> str:
    """
    Compress the image and transcode to Base64

    Args:
        pic_path: Img path

    Examples:
        img_base64 = await base_64(path)

    Return:
        str
    """
    size = os.path.getsize(pic_path) / 1024
    if size > 900:
        print('>>>>压缩<<<<')
        with IMG.open(pic_path) as img:
            w, h = img.size
            new_width = 500
            new_height = round(new_width / w * h)
            img = img.resize((new_width, new_height), IMG.ANTIALIAS)
            img_buffer = io.BytesIO()  # 生成buffer
            img.save(img_buffer, format='PNG', quality=70)
            byte_data = img_buffer.getvalue()
            base64_data = base64.b64encode(byte_data)
            code = base64_data.decode()
            return code
    with open(pic_path, 'rb') as f:
        coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        return coding.decode()


async def curl_md5(src: str) -> str:
    """
    MD5

    Args:
        src: sign

    Examples:
        sign = await curl_md5(sign)

    Return:
        str
    """
    m = hashlib.md5(src.encode('UTF-8'))
    return m.hexdigest().upper()


async def get_sign(params: dict) -> str:
    """
    Get sign of Tencent Ai Platform

    Args:
        params: Dict to send

    Examples:
        sign = await get_sign(params)

    Return:
        str
    """
    app_key = await get_config("txAppKey")
    params_keys = sorted(params.keys())
    sign = ""
    for i in params_keys:
        if params[i] != '':
            sign += "%s=%s&" % (i, parse.quote(params[i], safe=''))
    sign += "app_key=%s" % app_key
    sign = await curl_md5(sign)
    print("signMD5:", sign)
    return sign


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
    img_base64 = await base_64(path)
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
    params['sign'] = await get_sign(params)

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
