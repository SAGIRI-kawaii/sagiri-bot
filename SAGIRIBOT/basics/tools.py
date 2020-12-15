import io
import os
import base64
import hashlib
from urllib import parse
from PIL import Image as IMG
from PIL import Image, ImageDraw, ImageFont
import textwrap
import random

from SAGIRIBOT.basics.get_config import get_config


def subsection(string):
    return string.split('\n')


def carry(x, y):
    if x % y != 0:
        return x // y + 1
    return x // y


def insert_poster(sections, poster, num=3):
    if num > len(sections):
        num = len(sections)
    poster_pos = [random.randint(0, len(sections)) for _ in range(num)]
    for i in range(len(sections)):
        if i in poster_pos:
            sections[i] = sections[i] + poster
    return sections


def linefeed(sections, length):
    stringlins = []
    for section in sections:
        strs = textwrap.fill(section, length).split('\n')
        stringlins = stringlins + strs
    return stringlins


def text2lins(string, poster, length):
    segments = subsection(string);
    segments = insert_poster(segments, poster)
    string_lins = linefeed(segments, length)
    return string_lins


def text2piiic(string, poster, length, fontsize=20, x=20, y=40, spacing=20):
    lins = text2lins(string, poster, length)
    heigh = y * 2 + (fontsize + spacing) * len(lins)
    width = x * 2 + fontsize * length
    font = ImageFont.truetype('./simhei.ttf', fontsize, encoding="utf-8")
    picture = Image.new('RGB', (width, heigh), (255, 255, 255))
    draw = ImageDraw.Draw(picture)
    for i in range(len(lins)):
        y_pos = y + i * (fontsize + spacing)
        draw.text((x, y_pos), lins[i], font=font, fill=(0, 0, 0))
    return picture


def text2multigraph(string, poster, backdrop, fontsize=20, x=20, y=40, spacing=20):
    row = (backdrop.width - x * 2) // fontsize
    lin = carry((backdrop.height - y * 2), (fontsize + spacing))
    str_lin = text2lins(string, poster, row)
    str_lin_len = len(str_lin)
    num_lin = carry(str_lin_len, lin)
    font = ImageFont.truetype('simhei.ttf', fontsize, encoding="utf-8")
    imgs = []
    for num in range(num_lin):
        img = backdrop.copy()
        draw = ImageDraw.Draw(img)
        for i in range(lin):
            if (num * lin + i) < str_lin_len:
                draw.text((x, y + i * (fontsize + spacing)), str_lin[num * lin + i], font=font, fill=(0, 0, 0))
            else:
                break
        imgs.append(img)
    return imgs


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
