import re
import time
import aiohttp
import asyncio
import pypinyin
from bs4 import BeautifulSoup
from playwright._impl._api_types import TimeoutError

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graiax.playwright import PlaywrightBrowser
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from shared.utils.module_related import get_command
from shared.utils.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl, Distribute

channel = Channel.current()
channel.name("GenshinCharaCard")
channel.author("SAGIRI-kawaii")
channel.description("一个原神角色卡查询插件，在群中发送 `/原神角色卡 UID 角色名` 即可")

characters = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(r"[12][0-9]{8}") @ "uid",
                RegexMatch(r".*") @ "chara",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("genshin_chara_card", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def genshin_chara_card(app: Ariadne, group: Group, source: Source, uid: RegexResult, chara: RegexResult):
    start_time = time.time()
    uid = uid.result.display
    chara = chara.result.display.strip()
    chara_pinyin = "".join(pypinyin.lazy_pinyin(chara))
    if not characters:
        await app.send_group_message(group, MessageChain("正在初始化角色列表"))
        _ = await init_chara_list()
        await app.send_group_message(group, MessageChain("初始化完成"))
    if chara_pinyin not in characters:
        return await app.send_group_message(group, MessageChain(f"角色列表中未找到角色：{chara}，请检查拼写"))
    url = f"https://enka.shinshin.moe/u/{uid}"
    browser = Ariadne.current().launch_manager.get_interface(PlaywrightBrowser)
    async with browser.page() as page:
        await page.goto(url, wait_until="networkidle", timeout=100000)
        await page.set_viewport_size({"width": 2560, "height": 1080})
        await page.evaluate(
            "document.getElementsByClassName('Dropdown-list')[0].children[13].dispatchEvent(new Event('click'));"
        )
        html = await page.inner_html(".CharacterList")
        soup = BeautifulSoup(html, "html.parser")
        styles = [figure["style"] for figure in soup.find_all("figure")]
        if all(characters[chara_pinyin] not in style.lower() for style in styles):
            return await app.send_group_message(
                group,
                MessageChain(
                    f"未找到角色{chara} | {chara_pinyin}！只查询到这几个呢（只能查到展柜里有的呢）："
                    f"{'、'.join([k for k, v in characters.items() if any(v in style.lower() for style in styles)])}"
                ),
                quote=source,
            )
        index = -1
        chara_src = ""
        for i, style in enumerate(styles):
            if characters[chara_pinyin] in style.lower():
                index = i
                chara_src = style
                break
        if index == -1 or not chara_src:
            return await app.send_group_message(group, MessageChain("获取角色头像div失败！"))
        await page.locator(f"div.avatar.svelte-jlfv30 >> nth={index}").click()
        await asyncio.sleep(1)
        await page.get_by_role("button", name=re.compile("Export image", re.IGNORECASE)).click()
        async with page.expect_download() as download_info:
            for _ in range(3):
                try:
                    await page.get_by_role("button", name=re.compile("Download", re.IGNORECASE)).click(timeout=10000)
                except TimeoutError:
                    pass
        path = await (await download_info.value).path()
        await app.send_group_message(
            group,
            MessageChain([
                f"use: {round(time.time() - start_time, 2)}s\n",
                Image(path=path)
            ]),
            quote=source,
        )


async def init_chara_list():
    global characters
    url = "https://genshin.honeyhunterworld.com/fam_chars/?lang=CHS"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
    datas = re.findall(r"sortable_data.push\(\[(.*?)]\)", html, re.S)
    data = datas[0].replace(r"\"", '"').replace(r"\\", "\\").replace(r"\/", "/")
    cs = data[1:-1].split("],[")
    for c in cs:
        chn_name = re.findall(r'<img loading="lazy" alt="(.+?)"', c, re.S)[0]
        chn_name = chn_name.encode().decode("unicode_escape")
        en_name = re.findall(r'<a href="/(.+?)_.+/?lang=CHS"', c, re.S)[0]
        characters["".join(pypinyin.lazy_pinyin(chn_name))] = en_name.lower()
    print(characters)
