import io
import os
import base64
import hashlib
from urllib import parse
from PIL import Image as IMG
from PIL import ImageDraw, ImageFont
import textwrap
import random
import re
import qrcode
import math
import asyncio
import time
import aiohttp
from io import BytesIO
import aiofiles
import traceback

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Image_LocalFile

from SAGIRIBOT.basics.get_config import get_config


def subsection(string):
    return string.split('\n')


def carry(x, y):
    if x % y != 0:
        return x // y + 1
    return x // y


def is_chinese(ch):
    if '\u4e00' <= ch <= '\u9fff':
        return True
    return False


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
    width = x * 4 + fontsize * length
    font = ImageFont.truetype('./simhei.ttf', fontsize, encoding="utf-8")
    picture = IMG.new('RGB', (width, heigh), (255, 255, 255))
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
    # print(params_keys)
    sign = ""
    for i in params_keys:
        if params[i] != '':
            sign += "%s=%s&" % (i, parse.quote(params[i], safe=''))
    sign += "app_key=%s" % app_key
    sign = await curl_md5(sign)
    print("signMD5:", sign)
    return sign


async def filter_label(label_list: list) -> list:
    """
    Filter labels

    Args:
        label_list: Words to filter

    Examples:
        result = await filter_label(label_list)

    Return:
        list
    """
    not_filter = ["草"]
    image_filter = "mirai:"
    result = []
    for i in label_list:
        if image_filter in i:
            continue
        elif i in not_filter:
            result.append(i)
        elif len(i) != 1 and i.find('nbsp') < 0:
            result.append(i)
    return result


def count_len(string: str) -> int:
    length = 0
    for i in string:
        length += 2 if is_chinese(i) else 1
    return length


async def text2piiic_with_link(text: str, fontsize=40, x=20, y=40, spacing=15):
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    match_res = re.findall(pattern, text, re.S)
    for mres in match_res:
        text = text.replace(mres, "|||\n\n\n|||")
    for i in range(len(match_res)):
        qrcode_img = qrcode.make(match_res[i])
        qrcode_img.save(f"./statics/temp/tempQrcodeWithLink{i + 1}.jpg")
    blocks = text.split("|||\n\n\n|||")
    block_count = 0
    font = ImageFont.truetype('./simhei.ttf', fontsize, encoding="utf-8")
    for block in blocks:
        if not block or not block.strip():
            break
        block_count += 1
        lines = block.strip().split("\n")
        length = max(count_len(line) for line in lines)
        width = x * 4 + int(fontsize * (length + 10) / 2)
        height = y * 4 + (fontsize + spacing) * len(lines) + width
        qr_img = IMG.open(f"./statics/temp/tempQrcodeWithLink{block_count}.jpg")
        qr_img = qr_img.resize((width, width))
        picture = IMG.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(picture)
        for i in range(len(lines)):
            y_pos = y + i * (fontsize + spacing)
            draw.text((x, y_pos), lines[i], font=font, fill=(0, 0, 0))
        y_pos = y + len(lines) * (fontsize + spacing)
        picture.paste(qr_img, (0, y_pos))
        picture.save(f"./statics/temp/tempText2piiicWithLink{block_count}.jpg")

    return [
        f"./statics/temp/tempText2piiicWithLink{i + 1}.jpg" for i in range(block_count)
    ]


async def get_final_text_lines(text: str, text_width: int, font: ImageFont.FreeTypeFont) -> int:
    lines = text.split("\n")
    line_count = 0
    for line in lines:
        if not line:
            line_count += 1
            continue
        line_count += int(math.ceil(float(font.getsize(line)[0]) / float(text_width)))
    print("lines: ", line_count + 1)
    return line_count + 1


async def messagechain_to_img(
        message: MessageChain,
        max_width: int = 1080,
        font_size: int = 40,
        spacing: int = 15,
        padding_x: int = 20,
        padding_y: int = 15,
        img_fixed: bool = False,
        font_path: str = "./simhei.ttf",
        save_path: str = "./statics/temp/tempMessageChainToImg.png"
) -> MessageChain:
    """
    将 MessageChain 转换为图片，仅支持只含有本地图片/文本的 MessageChain

    Args:
        message: 要转换的MessageChain
        max_width: 最大长度
        font_size: 字体尺寸
        spacing: 行间距
        padding_x: x轴距离边框大小
        padding_y: y轴距离边框大小
        img_fixed: 图片是否适应大小（仅适用于图片小于最大长度时）
        font_path: 字体文件路径
        save_path: 图片存储路径

    Examples:
        msg = await messagechain_to_img(message=message)

    Returns:
        MessageChain （内含图片Image类）
    """
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    message = message.asMerged()
    elements = message.__root__

    plains = message.get(Plain)
    text_gather = "\n".join([plain.text for plain in plains])
    print(max(font.getsize(text)[0] for text in text_gather.split("\n")) + 2 * padding_x)
    final_width = min(max(font.getsize(text)[0] for text in text_gather.split("\n")) + 2 * padding_x, max_width)
    text_width = final_width - 2 * padding_x
    text_height = (font_size + spacing) * await get_final_text_lines(text_gather, text_width, font)
    # text_height = (font_size + spacing) * sum([await get_final_text_lines(plain.text, text_width, font)for plain in plains])

    img_height_sum = 0
    temp_img_list = []
    images = message.get(Image_LocalFile)
    for image in images:
        if isinstance(image, Image_LocalFile):
            # print(img_height_sum)
            temp_img = IMG.open(image.filepath)
            # print(temp_img.size)
            img_width, img_height = temp_img.size
            temp_img_list.append(
                temp_img := temp_img.resize(
                    (
                        int(final_width - 2 * spacing),
                        int(float(img_height * (final_width - 2 * spacing)) / float(img_width))
                    )
                ) if img_width > final_width - 2 * spacing or (img_fixed and img_width < final_width - 2 * spacing)
                else temp_img
            )
            img_height_sum = img_height_sum + temp_img.size[1]
            # print(temp_img.size[1])
            # print(img_height)
        else:
            raise Exception("messagechain_to_img：仅支持本地图片即Image_LocalFile类的处理！")
    final_height = 2 * padding_y + text_height + img_height_sum
    picture = IMG.new('RGB', (final_width, final_height), (255, 255, 255))
    draw = ImageDraw.Draw(picture)
    present_x = padding_x
    present_y = padding_y
    image_index = 0
    # print(temp_img_list)
    for element in elements:
        if isinstance(element, Image_LocalFile):
            print(f"adding img {image_index}")
            picture.paste(temp_img_list[image_index], (present_x, present_y))
            present_y += (spacing + temp_img_list[image_index].size[1])
            image_index += 1
        elif isinstance(element, Plain):
            print(f"adding text '{element.text}'")
            # if font.getsize(element.text)[0] <= text_width:
            #     draw.text((present_x, present_y), element.text, font=font, fill=(0, 0, 0))
            # else:
            for char in element.text:
                if char == "\n":
                    present_y += (font_size + spacing)
                    present_x = padding_x
                    continue
                if present_x + font.getsize(char)[0] > text_width:
                    present_y += (font_size + spacing)
                    present_x = padding_x
                draw.text((present_x, present_y), char, font=font, fill=(0, 0, 0))
                present_x += font.getsize(char)[0]
            present_y += (font_size + spacing)
            present_x = padding_x

    # print(f"textHeight: {text_height}\nimgHeight: {img_height}\nfinalHeight: {final_height}")
    # print(f"present_x: {present_x}, present_y: {present_y}")
    picture.save(save_path)
    print(f"process finished! Image saved at {save_path}")
    return MessageChain.create([
        Image.fromLocalFile(save_path)
    ])


async def save_img(image: Image) -> str:
    path = "./statics/temp/tempSavedImage.jpg"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=image.url) as resp:
            img_content = await resp.read()
            image = IMG.open(BytesIO(img_content))
            image.save(path)
    return path


async def silk(data, mtype='b', options=''):
    try:
        cache_files = ['./statics/temp/cache.wav']
        # , './statics/temp/cache.slk'

        if mtype == 'f':
            file = data
        elif mtype == 'b':
            async with aiofiles.open('./statics/temp/music_cache', 'wb') as f:
                await f.write(data)
            file = './statics/temp/music_cache'
            cache_files.append(file)
        else:
            raise ValueError("Not fit music_type. only 'f' and 'b'")

        cmd = [f'ffmpeg -i "{file}" {options} -af aresample=resampler=soxr -ar 8000 -ac 1 -y -loglevel error "./statics/temp/cache.wav"',]
        # f'"lib/silk_v3_encoder.exe" ./statics/temp/cache.wav ./statics/temp/cache.slk -quiet -tencent'

        for p in cmd:
            shell = await asyncio.create_subprocess_shell(p)
            await shell.wait()

        print(1)

        async with aiofiles.open(f'./statics/temp/cache.wav', 'rb') as f:
            b = await f.read()
        # 清除cache
        # for cache_file in cache_files:
        #     await aiofiles.os.remove(cache_file)
        # for cache_file in cache_files:
        #     os.remove(cache_file)
        return b
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    message = MessageChain.create([
        Plain("test"),
        Plain(
            "和商务大厦记得哈施工单位与其哎呀和商务大厦记得哈施工\n\n\n\n单位与其哎呀和商务大厦记得哈施工单位与其哎呀和商务大厦记得哈施工单位与其哎呀和商务大厦记得哈施工单位与其哎呀和商务大厦记得哈施工单位与其哎呀和商务大厦记得哈施工单位与其哎呀和商务大厦记得哈施工单位与其哎呀"),
        Plain(
            "asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施\n\n\n\n工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与其哎呀"),
        Image.fromLocalFile("M:\pixiv\pxer_new\\1001.png"),
        Plain(
            "asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与\n\n\n\nasdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与其哎呀"),
        Image.fromLocalFile("M:\pixiv\pxer_new\\1002.png"),
        Plain(
            "asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyqu\n\n\n\nwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与asdbyquwbgyuedg1阿瑟帝国与邱2 1和商务大厦记得哈施工单位与其哎呀")
    ])
    loop = asyncio.get_event_loop()
    start = time.time()
    loop.run_until_complete(messagechain_to_img(message=message, max_width=1400))
    print(time.time() - start)
