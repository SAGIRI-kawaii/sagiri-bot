import aiohttp
from graia.saya import Channel
from graia.ariadne.app import Ariadne

from graiax.playwright import PlaywrightBrowser
from graia.ariadne.exception import MessageTooLong
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    ArgumentMatch,
    RegexResult,
    WildcardMatch,
    ArgResult,
)

from shared.utils.text2img import md2img
from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("GithubInfo")
channel.author("SAGIRI-kawaii")
channel.description("可以搜索Github项目信息的插件，在群中发送 `/github [-i] {项目名}`")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-i", "-image", action="store_true", optional=True) @ "image",
                ArgumentMatch("-s", "-screenshot", action="store_true", optional=True) @ "screenshot",
                WildcardMatch() @ "keyword",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("github_info", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def github_info(
    app: Ariadne, group: Group, source: Source, image: ArgResult, screenshot: ArgResult, keyword: RegexResult
):
    image = image.matched
    screenshot = screenshot.matched
    keyword = keyword.result.display
    url = "https://api.github.com/search/repositories?q="
    img_url = "https://opengraph.githubassets.com/c9f4179f4d560950b2355c82aa2b7750bffd945744f9b8ea3f93cc24779745a0/"
    if screenshot:
        browser = Ariadne.current().launch_manager.get_interface(PlaywrightBrowser)
        screenshot_url = f"https://github.com/{keyword}"
        async with browser.page() as page:
            await page.goto(screenshot_url, wait_until="networkidle", timeout=100000)
            await page.evaluate("document.getElementsByClassName('Layout-sidebar')[0].remove()")
            await page.evaluate("document.getElementsByClassName('js-header-wrapper')[0].remove()")
            await page.evaluate("document.getElementsByClassName('footer')[0].remove()")
            await page.evaluate("document.getElementsByClassName('gh-header-actions')[0].remove()")
            await page.evaluate("document.getElementsByClassName('discussion-timeline-actions')[0].remove()")
            await page.evaluate("document.getElementsByClassName('js-repo-nav')[0].remove()")
            await page.evaluate(
                "document.getElementsByClassName('Layout--flowRow-until-md')[0].classList.remove('Layout')"
            )
            buffer = await page.screenshot(full_page=True)
            return await app.send_group_message(group, MessageChain(Image(data_bytes=buffer)))
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url + keyword) as resp:
            result = (await resp.json())["items"]
    if not result:
        await app.send_group_message(group, MessageChain("没有搜索到结果呢~"), quote=source)
    elif image:
        img_url += result[0]["full_name"]
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp:
                content = await resp.read()
        await app.send_group_message(
            group, MessageChain(Image(data_bytes=content)), quote=source
        )
    else:
        result = result[0]
        name = result["name"]
        owner = result["owner"]["login"]
        description = result["description"]
        repo_url = result["html_url"]
        stars = result["stargazers_count"]
        watchers = result["watchers"]
        language = result["language"]
        forks = result["forks"]
        issues = result["open_issues"]
        repo_license = result["license"]["key"] if result["license"] else "无"
        msg = MessageChain(
            f"名称：{name}\n"
            f"作者：{owner}\n"
            f"描述：{description}\n"
            f"链接：{repo_url}\n"
            f"stars：{stars}\n"
            f"watchers：{watchers}\n"
            f"forks：{forks}\n"
            f"issues：{issues}\n"
            f"language：{language}\n"
            f"license：{repo_license}"
        )
        try:
            await app.send_group_message(group, msg, quote=source)
        except MessageTooLong:
            image = await md2img(
                msg.display.replace("\n", "<br>"),
                {"viewport": {"width": 500, "height": 10}}
            )
            await app.send_group_message(
                group,
                MessageChain(Image(data_bytes=image)),
                quote=source,
            )
