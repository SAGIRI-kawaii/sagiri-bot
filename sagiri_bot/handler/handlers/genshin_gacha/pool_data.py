import re
import os
import json
import time
import aiohttp
import collections
from io import BytesIO
from loguru import logger
from PIL import Image, ImageFont, ImageDraw, ImageMath

FILE_PATH = os.path.dirname(__file__)
ICON_PATH = os.path.join(FILE_PATH, 'icon')
FONT_PATH = os.path.join(FILE_PATH, "zh-cn.ttf")
AUTO_UPDATE = True

POOL_API = "https://webstatic.mihoyo.com/hk4e/gacha_info/cn_gf01/gacha/list.json"
ROLES_API = ['https://genshin.honeyhunterworld.com/db/char/characters/?lang=CHS',
             'https://genshin.honeyhunterworld.com/db/char/unreleased-and-upcoming-characters/?lang=CHS']
ARMS_API = ['https://genshin.honeyhunterworld.com/db/weapon/sword/?lang=CHS',
            'https://genshin.honeyhunterworld.com/db/weapon/claymore/?lang=CHS',
            'https://genshin.honeyhunterworld.com/db/weapon/polearm/?lang=CHS',
            'https://genshin.honeyhunterworld.com/db/weapon/bow/?lang=CHS',
            'https://genshin.honeyhunterworld.com/db/weapon/catalyst/?lang=CHS']
ROLES_HTML_LIST = None
ARMS_HTML_LIST = None

FONT = ImageFont.truetype(FONT_PATH, size=20)

# 这个字典记录的是3个不同的卡池，每个卡池的抽取列表
POOL = collections.defaultdict(
    lambda: {
        '5_star_UP': [],
        '5_star_not_UP': [],
        '4_star_UP': [],
        '4_star_not_UP': [],
        '3_star_not_UP': []
    })


async def get_url_data(url):
    # 获取url的数据
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as resp:
            if resp.status != 200:
                raise ValueError(f"从 {url} 获取数据失败，错误代码 {resp.status}")
            return await resp.read()


async def get_role_en_name(ch_name):
    # 从 genshin.honeyhunterworld.com 获取角色的英文名
    global ROLES_HTML_LIST
    if ROLES_HTML_LIST is None:
        ROLES_HTML_LIST = []
        for api in ROLES_API:
            data = await get_url_data(api)
            ROLES_HTML_LIST.append(data.decode("utf-8"))

    pattern = ".{80}" + str(ch_name)
    for html in ROLES_HTML_LIST:
        txt = re.search(pattern, html)
        if txt is None:
            continue
        txt = re.search('"/db/char/.+/\?lang=CHS"', txt.group()).group()
        return txt[10:-11]
    raise NameError(f"没有找到角色 {ch_name} 的图标名")


async def get_arm_id(ch_name):
    # 从 genshin.honeyhunterworld.com 获取武器的ID
    global ARMS_HTML_LIST
    if ARMS_HTML_LIST is None:
        ARMS_HTML_LIST = []
        for api in ARMS_API:
            data = await get_url_data(api)
            ARMS_HTML_LIST.append(data.decode("utf-8"))

    pattern = '.{40}' + str(ch_name)
    for html in ARMS_HTML_LIST:
        txt = re.search(pattern, html)
        if txt is None:
            continue
        txt = re.search('weapon/.+?/\?lang', txt.group()).group()
        arm_id = txt[7:-6]
        return arm_id
    raise NameError(f"没有找到武器 {ch_name} 的 ID")


async def get_icon(url):
    # 获取角色或武器的图标，直接返回 Image
    icon = await get_url_data(url)
    icon = Image.open(BytesIO(icon))
    icon_a = icon.getchannel("A")
    icon_a = ImageMath.eval("convert(a*b/256, 'L')", a=icon_a, b=icon_a)
    icon.putalpha(icon_a)
    return icon


async def get_role_element(en_name):
    # 获取角色属性，直接返回属性图标 Image
    url = f'https://genshin.honeyhunterworld.com/db/char/{en_name}/?lang=CHS'
    data = await get_url_data(url)
    data = data.decode("utf-8")
    element = re.search('/img/icons/element/.+?_35.png', data).group()
    element = element[19:-7]

    element_path = os.path.join(FILE_PATH, 'icon', f'{element}.png')
    return Image.open(element_path)


async def paste_role_icon(ch_name, star):
    # 拼接角色图鉴图

    en_name = await get_role_en_name(ch_name)
    url = f"https://genshin.honeyhunterworld.com/img/char/{en_name}_face.png"
    avatar_icon = await get_icon(url)
    element_icon = await get_role_element(en_name)

    bg = Image.open(os.path.join(FILE_PATH, 'icon', f'{star}_star_bg.png'))
    bg_a = bg.getchannel("A")
    bg1 = Image.new("RGBA", bg.size)
    txt_bg = Image.new("RGBA", (160, 35), "#e9e5dc")
    x = int(160 / 256 * avatar_icon.size[0])
    avatar_icon = avatar_icon.resize((x, 160))
    element_icon = element_icon.resize((40, 40))
    x_pos = int(160 / 2 - x / 2)
    bg.paste(avatar_icon, (x_pos, 3), avatar_icon)
    bg.paste(element_icon, (2, 3), element_icon)
    bg.paste(txt_bg, (0, 163))
    draw = ImageDraw.Draw(bg)
    draw.text((80, 180), ch_name, fill="#4a5466ff", font=FONT, anchor="mm", align="center")
    bg1.paste(bg, (0, 0), bg_a)
    return bg1


async def paste_arm_icon(ch_name, star):
    # 拼接武器图鉴图
    arm_id = await get_arm_id(ch_name)
    url = f'https://genshin.honeyhunterworld.com/img/weapon/{arm_id}_a.png'
    arm_icon = await get_icon(url)
    star_icon = Image.open(os.path.join(FILE_PATH, 'icon', f'{star}_star.png'))

    bg = Image.open(os.path.join(FILE_PATH, 'icon', f'{star}_star_bg.png'))
    bg_a = bg.getchannel("A")
    bg1 = Image.new("RGBA", bg.size)
    txt_bg = Image.new("RGBA", (160, 35), "#e9e5dc")
    x = int(160 / arm_icon.size[1] * arm_icon.size[0])
    arm_icon = arm_icon.resize((x, 160))
    x_pos = int(155 / 2 - x / 2)
    bg.paste(arm_icon, (x_pos, 3), arm_icon)
    bg.paste(txt_bg, (0, 163))
    draw = ImageDraw.Draw(bg)
    draw.text((80, 180), ch_name, fill="#4a5466ff", font=FONT, anchor="mm", align="center")
    bg.paste(star_icon, (6, 135), star_icon)
    bg1.paste(bg, (0, 0), bg_a)
    return bg1


async def up_role_icon(name, star):
    # 更新角色图标
    role_name_path = os.path.join(ICON_PATH, "角色图鉴", str(name) + ".png")
    if os.path.exists(role_name_path):
        return
    logger.info(f"正在更新 {name} 角色图标")
    if not os.path.exists(os.path.join(ICON_PATH, '角色图鉴')):
        os.makedirs(os.path.join(ICON_PATH, '角色图鉴'))

    try:
        role_icon = await paste_role_icon(name, star)
        with open(role_name_path, "wb") as icon_file:
            role_icon.save(icon_file)
    except Exception as e:
        logger.error(f"更新 {name} 角色图标失败，错误为 {e},建议稍后使用 更新原神卡池 指令重新更新")


async def up_arm_icon(name, star):
    # 更新武器图标
    arm_name_path = os.path.join(ICON_PATH, "武器图鉴", str(name) + ".png")
    if os.path.exists(arm_name_path):
        return
    logger.info(f"正在更新 {name} 武器图标")
    if not os.path.exists(os.path.join(ICON_PATH, '武器图鉴')):
        os.makedirs(os.path.join(ICON_PATH, '武器图鉴'))

    try:
        arm_icon = await paste_arm_icon(name, star)
        with open(arm_name_path, "wb") as icon_file:
            arm_icon.save(icon_file)
    except Exception as e:
        logger.error(f"更新 {name} 武器图标失败，错误为 {e},建议稍后使用 更新原神卡池 指令重新更新")


async def init_pool_list():
    # 初始化卡池数据
    global ROLES_HTML_LIST
    global ARMS_HTML_LIST

    ROLES_HTML_LIST = None
    ARMS_HTML_LIST = None
    POOL.clear()

    logger.info(f"正在更新卡池数据")
    data = await get_url_data(POOL_API)
    data = json.loads(data.decode("utf-8"))
    for d in data["data"]["list"]:

        begin_time = time.mktime(time.strptime(d['begin_time'], "%Y-%m-%d %H:%M:%S"))
        end_time = time.mktime(time.strptime(d['end_time'], "%Y-%m-%d %H:%M:%S"))
        if not (begin_time < time.time() < end_time):
            continue

        pool_name = str(d['gacha_name'])
        pool_url = f"https://webstatic.mihoyo.com/hk4e/gacha_info/cn_gf01/{d['gacha_id']}/zh-cn.json"
        pool_data = await get_url_data(pool_url)
        pool_data = json.loads(pool_data.decode("utf-8"))

        for prob_list in ['r3_prob_list', 'r4_prob_list', 'r5_prob_list']:
            for i in pool_data[prob_list]:
                item_name = i['item_name']
                item_type = i["item_type"]
                item_star = str(i["rank"])
                key = ''
                key += item_star
                key += "_star_UP" if str(i["is_up"]) == "1" else "_star_not_UP"
                POOL[pool_name][key].append(item_name)

                if item_type == '角色':
                    await up_role_icon(name=item_name, star=item_star)
                else:
                    await up_arm_icon(name=item_name, star=item_star)
