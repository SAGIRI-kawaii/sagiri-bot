import io
import os
import base64
import hashlib
from urllib import parse
from PIL import Image as IMG

from SAGIRIBOT.basics.get_config import get_config


async def img_to_base_64(pic_path: str) -> str:
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


async def get_tx_sign(params: dict) -> str:
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
