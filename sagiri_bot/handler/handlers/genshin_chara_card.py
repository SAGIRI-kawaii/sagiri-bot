import time
import pypinyin
from bs4 import BeautifulSoup

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult

from utils.browser import get_browser
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("GenshinCharaCard")
channel.author("SAGIRI-kawaii")
channel.description("一个原神角色卡查询插件，在群中发送 `/原神角色卡 UID 角色名` 即可")

proxy = AppCore.get_core_instance().get_config().proxy
proxy = proxy if proxy != "proxy" else None

characters = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/原神角色卡"),
                RegexMatch(r"[12][0-9]{8}") @ "uid",
                RegexMatch(r".*") @ "chara"
            ])
        ],
        decorators=[
            FrequencyLimit.require("genshin_chara_card", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def genshin_chara_card(app: Ariadne, group: Group, source: Source, uid: RegexResult, chara: RegexResult):
    start_time = time.time()
    uid = uid.result.asDisplay()
    chara = chara.result.asDisplay().strip()
    chara_pinyin = ''.join(pypinyin.lazy_pinyin(chara))
    if not characters:
        await app.sendGroupMessage(group, MessageChain("正在初始化角色列表"))
        _ = await init_chara_list()
        await app.sendGroupMessage(group, MessageChain("初始化完成"))
    if chara_pinyin not in characters:
        return await app.sendGroupMessage(group, MessageChain(f"角色列表中未找到角色：{chara}，请检查拼写"))
    url = f"https://enka.shinshin.moe/u/{uid}"
    if proxy:
        browser = await get_browser(proxy={"server": proxy})
    else:
        browser = await get_browser()
    if not browser:
        return await app.sendGroupMessage(group, MessageChain("获取browser失败！"))
    try:
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=100000)
        await page.set_viewport_size({"width": 2560, "height": 1080})
        await page.evaluate(
            "document.getElementsByClassName('Dropdown-list')[0].children[13].dispatchEvent(new Event('click'));"
        )
        html = await page.inner_html(".CharacterList")
        soup = BeautifulSoup(html, "html.parser")
        styles = [figure["style"] for figure in soup.find_all("figure")]
        # print(styles)
        if all(characters[chara_pinyin] not in style.lower() for style in styles):
            await page.close()
            await browser.close()
            return await app.sendGroupMessage(
                group,
                MessageChain(
                    f"未找到角色{chara} | {chara_pinyin}！只查询到这几个呢（只能查到展柜里有的呢）："
                    f"{'、'.join([k for k, v in characters.items() if any(v in style.lower() for style in styles)])}"
                ),
                quote=source
            )
        else:
            index = -1
            chara_src = ""
            for i, style in enumerate(styles):
                if characters[chara_pinyin] in style.lower():
                    index = i
                    chara_src = style
                    break
            if index == -1 or not chara_src:
                return await app.sendGroupMessage(group, MessageChain("获取角色头像div失败！"))
            await page.locator(f'div.avatar.svelte-188i0pk >> nth={index}').click()
            await page.locator('div.Card.svelte-m3ch8z').wait_for()
            # await page.locator('canvas.svelte-d1gpxk').wait_for()
            # await page.locator('img.WeaponIcon.svelte-gp6viv').wait_for()
            # await page.locator('canvas.ArtifactIcon').wait_for()
            buffer = await page.locator('div.Card.svelte-m3ch8z').screenshot()
            await page.close()
            await browser.close()
            await app.sendGroupMessage(
                group,
                MessageChain([
                    f"use: {round(time.time() - start_time, 2)}s\n",
                    Image(data_bytes=buffer)
                ]),
                quote=source
            )
    except:
        await browser.close()


async def init_chara_list():
    global characters
    url = "https://genshin.honeyhunterworld.com/db/char/characters/?lang=CHS"
    async with get_running(Adapter).session.get(url) as resp:
        html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", {"class": "char_sea_cont"})
    for div in divs:
        a = div.find_all("a")
        name = ''.join(pypinyin.lazy_pinyin(a[1].get_text().strip()))
        eng_name = a[0]["href"].split('/')[3]
        characters[name] = eng_name.lower()
    print(characters)


async def generate_card(uid: int):
    url = f"https://enka.shinshin.moe/u/{uid}/__data.json"
    async with get_running(Adapter).session.get(url) as resp:
        result = await resp.json()
