import os
import time
import asyncio
from typing import List
from pathlib import Path
from datetime import datetime, timedelta

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.twilight import FullMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, Sparkle

from utils.browser import get_browser
from sagiri_bot.utils import BuildImage
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import QuoteSource
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.decorators import frequency_limit_require_weight_free
from sagiri_bot.utils import update_user_call_count_plus, UserCalledCount

saya = Saya.current()
channel = Channel.current()

channel.name("GenshinMaterialRemind")
channel.author("SAGIRI-kawaii")
channel.description("一个可以查询原神每日可获取素材的插件，在群中发送 `原神今日素材` 即可")

core = AppCore.get_core_instance()
config = core.get_config()
proxy = config.proxy if config.proxy != "proxy" else ''
IMAGE_PATH = Path.cwd() / "statics" / "genshin" / "material"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([FullMatch("原神今日素材")]))]
    )
)
async def genshin_material_remind(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await GenshinMaterialRemind.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class GenshinMaterialRemind(AbstractHandler):
    __name__ = "GenshinMaterialRemind"
    __description__ = "一个可以查询原神每日可获取素材的插件"
    __usage__ = "在群中发送 `原神今日素材` 即可"

    @staticmethod
    @switch()
    @blacklist()
    @frequency_limit_require_weight_free(1)
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        await update_user_call_count_plus(group, member, UserCalledCount.functions, "functions")
        if time.strftime("%w") == "0":
            return MessageItem(MessageChain.create([Plain(text="今天是周日，所有材料副本都开放了。")]), QuoteSource())
        file_name = str((datetime.now() - timedelta(hours=4)).date())
        if not (Path(IMAGE_PATH) / f"{file_name}.png").exists():
            await app.sendMessage(group, MessageChain.create([Plain(text="正在自动更新中...")]))
            _ = await GenshinMaterialRemind.update_image()
            print(_)
        return MessageItem(
            MessageChain.create([
                Image(path=Path(IMAGE_PATH) / f"{file_name}.png"),
                Plain(text="\n※ 每日素材数据来源于 genshin.pub")
            ]),
            QuoteSource()
        )

    @staticmethod
    async def update_image():
        page = None
        # try:
        if not os.path.exists(str(IMAGE_PATH)):
            os.makedirs(str(IMAGE_PATH))
        for file in os.listdir(str(IMAGE_PATH)):
            os.remove(str(IMAGE_PATH / file))
        browser = await get_browser()
        if not browser:
            raise ValueError("获取browser失败！")
        url = "https://genshin.pub/daily"
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=100000)
        await page.set_viewport_size({"width": 2560, "height": 1080})
        await page.evaluate(
            """
            document.getElementsByClassName('GSTitleBar_gs_titlebar__2IJqy')[0].remove();
            e = document.getElementsByClassName('GSContainer_gs_container__2FbUz')[0];
            e.setAttribute("style", "height:880px");
        """
        )
        await page.click("button")
        div = await page.query_selector(".GSContainer_content_box__1sIXz")
        for i, card in enumerate(
                await page.query_selector_all(".GSTraitCotainer_trait_section__1f3bc")
        ):
            index = 0
            type_ = "char" if not i else "weapons"
            for x in await card.query_selector_all("xpath=child::*"):
                await x.screenshot(
                    path=f"{IMAGE_PATH}/{type_}_{index}.png",
                    timeout=100000,
                )
                # 下滑两次
                for _ in range(3):
                    await div.press("PageDown")
                index += 1
            # 结束后上滑至顶
            for _ in range(index * 3):
                await div.press("PageUp")
        file_list = os.listdir(str(IMAGE_PATH))
        char_imgs = [
            f"{IMAGE_PATH}/{x}"
            for x in file_list
            if x.startswith("char")
        ]
        weapons_imgs = [
            f"{IMAGE_PATH}/{x}"
            for x in file_list
            if x.startswith("weapons")
        ]
        char_imgs.sort()
        weapons_imgs.sort()
        height = await asyncio.get_event_loop().run_in_executor(
            None, GenshinMaterialRemind.get_background_height, weapons_imgs
        )
        background_img = BuildImage(1200, height + 100, color="#f6f2ee")
        current_width = 50
        for imgs in [char_imgs, weapons_imgs]:
            current_height = 20
            for img in imgs:
                x = BuildImage(0, 0, background=img)
                background_img.paste(x, (current_width, current_height))
                current_height += x.size[1]
            current_width += 600
        file_name = str((datetime.now() - timedelta(hours=4)).date())
        background_img.save(f"{IMAGE_PATH}/{file_name}.png")
        await page.close()
        return True
        # except Exception as e:
        #     logger.error(f"原神每日素材更新出错... {type(e)}: {e}")
        #     if page:
        #         await page.close()
        #     return False

    @staticmethod
    def get_background_height(weapons_imgs: List[str]) -> int:
        height = 0
        for weapons in weapons_imgs:
            height += BuildImage(0, 0, background=weapons).size[1]
        last_weapon = BuildImage(0, 0, background=weapons_imgs[-1])
        w, h = last_weapon.size
        last_weapon.crop((0, 0, w, h - 10))
        last_weapon.save(weapons_imgs[-1])

        return height
