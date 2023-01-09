import aiohttp
from bs4 import BeautifulSoup

from creart import create
from graia.saya import Channel
from graia.ariadne import Ariadne
from graiax.playwright import PlaywrightBrowser
from graia.ariadne.message.element import Image
from graia.ariadne.model.relationship import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, WildcardMatch, RegexResult, ArgumentMatch, ArgResult

from shared.models.config import GlobalConfig
from shared.utils.module_related import get_command
from shared.utils.control import Distribute, Function, BlackListControl

channel = Channel.current()
channel.name("AVBT")
channel.author("SAGIRI-kawaii")
channel.description("这是一个示例插件")

url = "https://sukebei.nyaa.si"
proxy = create(GlobalConfig).get_proxy()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-i", "-image", action="store_true") @ "has_img",
                WildcardMatch() @ "keyword"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module),
            BlackListControl.enable()
        ]
    )
)
async def av_bt(app: Ariadne, group: Group, has_img: ArgResult, keyword: RegexResult):
    keyword = keyword.result.display.strip()
    if not keyword:
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/?q={keyword}", proxy=proxy) as resp:
            html = await resp.read()
        soup = BeautifulSoup(html, "html.parser")
        href = soup.find("table").find("tbody").find("tr").find_all("a")[1]["href"]
        view_url = url + href
        async with session.get(view_url, proxy=proxy) as resp:
            html = await resp.read()
        soup = BeautifulSoup(html, "html.parser")
        panels = soup.find_all("div", {"class": "panel"})[:-1]
        magnet = panels[0].find("div", {"class": "panel-footer"}).find_all("a")[1]["href"]
        browser = Ariadne.current().launch_manager.get_interface(PlaywrightBrowser)
        async with browser.page() as page:
            await page.goto(view_url, wait_until="networkidle", timeout=100000)
            await page.evaluate("document.getElementById('dd4ce992-766a-4df0-a01d-86f13e43fd61').remove()")
            await page.evaluate("document.getElementById('e7a3ddb6-efae-4f74-a719-607fdf4fa1a1').remove()")
            await page.evaluate("document.getElementById('comments').remove()")
            await page.evaluate("document.getElementsByTagName('nav')[0].remove()")
            await page.evaluate("document.getElementsByTagName('footer')[0].remove()")
            if not has_img.matched:
                await page.evaluate("var a = document.getElementsByClassName('panel')[1].getElementsByTagName('img');while(a.length > 0){a[0].remove()}")
            content = await page.screenshot(full_page=True)
        return await app.send_message(
            group, MessageChain([
                Image(data_bytes=content),
                f"\n{magnet}"
            ])
        )
