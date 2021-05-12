import re
import json
import aiohttp
import asyncio
from bs4 import BeautifulSoup

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, Image

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource
from SAGIRIBOT.static_datas import lol_hero_name_to_code


class LOLItemRaidersHandler(AbstractHandler):
    __name__ = "LOLItemRaidersHandler"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r"lol .* .*", message.asDisplay()):
            pass
        elif re.match(r"lol .*", message.asDisplay()):
            pass
        else:
            return await super().handle(app, message, group, member)

    @staticmethod
    async def get_img_rates(tr):
        tds = tr.find_all("td")
        imgs = ["https:" + img["src"] for img in tds[0].find_all("img")]
        while "https://opgg-static.akamaized.net/images/site/champion/blet.png" in imgs:
            imgs.remove("https://opgg-static.akamaized.net/images/site/champion/blet.png")
        appearance_rate = tds[1].find("strong").get_text().strip()
        win_rate = tds[2].find("strong").get_text().strip()
        return {
            "images": imgs,
            "appearance_rate": appearance_rate,
            "win_rate": win_rate
        }

    @staticmethod
    async def get_hero_statics(hero_name: str, hero_position: str) -> MessageItem:
        if hero_name in lol_hero_name_to_code.keys():
            hero_name = lol_hero_name_to_code[hero_name]
        if hero_name not in lol_hero_name_to_code.values():
            return MessageItem(MessageChain.create([Plain(text="没有找到呢～看看是不是英雄名字打错了呐～")]), QuoteSource(GroupStrategy()))
        headers = {"accept-language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6"}
        url = f"https://www.op.gg/champion/{hero_name}/statistics/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as resp:
                html = await resp.read()
        soup = BeautifulSoup(html, "html.parser")
        lis = soup.find_all("li", {"class": "champion-stats-header__position"})
        positions = [li["data-position"].lower() for li in lis]
        print(positions)
        if hero_position.lower() not in positions:
            return MessageItem(
                MessageChain.create([Plain(text=f"没有这个位置呢～{hero_name}的位置只有" + "、".join(positions) + "呢！")]),
                QuoteSource(GroupStrategy())
            )
        data = {}
        url = f"https://www.op.gg/champion/{hero_name}/statistics/{hero_position}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as resp:
                html = await resp.read()
        soup = BeautifulSoup(html, "html.parser")

        summoner_spell_table = soup.find_all("table", {"class": "champion-overview__table champion-overview__table--summonerspell"})[0]
        trs = summoner_spell_table.find_all("tr")[1:]
        for tr in trs[:2]:
            print(await LOLItemRaidersHandler.get_img_rates(tr))
        skill_imgs = ["https:" + img["src"] for img in trs[3].find_all("ul", {"class": "champion-stats__list"})[0].find_all("img")]
        while "https://opgg-static.akamaized.net/images/site/champion/blet.png" in skill_imgs:
            skill_imgs.remove("https://opgg-static.akamaized.net/images/site/champion/blet.png")
        print(skill_imgs)
        overview_table = soup.find_all("table", {"class": "champion-overview__table"})[1]
        split_tr = overview_table.find_all("tr", {"class": "champion-overview__row champion-overview__row--first"})
        print(len(split_tr))
        item_constructions = [[], [], []]
        index = -1
        for tr in overview_table.find_all("tr", {"class": "champion-overview__row"}):
            if tr in split_tr:
                index += 1
            item_constructions[index].append(tr)

        # 初始装备
        trs = item_constructions[0]
        for tr in trs:
            print(await LOLItemRaidersHandler.get_img_rates(tr))

        # 推荐建设
        trs = item_constructions[1]
        for tr in trs:
            print(await LOLItemRaidersHandler.get_img_rates(tr))

        # 鞋子
        trs = item_constructions[2]
        for tr in trs:
            print(await LOLItemRaidersHandler.get_img_rates(tr))

        rune_table = soup.find_all("table", {"class": "champion-overview__table champion-overview__table--rune tabItems"})[0]
        tbodys = rune_table.find_all("tbody")[1:]

        rune_data = []

        for tbody in tbodys:
            trs = tbody.find_all("tr")
            rune_divs = trs[0].find_all("div", {"class": "perk-page-wrap"})
            for rune_div in rune_divs:
                row_data_imgs = []
                rune_div_pages = rune_div.find_all("div", {"class": "perk-page"})
                rune_div_fragment = rune_div.find_all("div", {"class": "fragment-page"})[0]
                for rune_div_page in rune_div_pages:
                    row_imgs = []
                    rows = rune_div_page.find_all("div", {"class": "perk-page__row"})
                    row_imgs.append("https:" + rows[0].find_all("img")[0]["src"])
                    for row in rows[1:]:
                        row_img = ["https:" + img["src"] for img in row.find_all("img")]
                        row_imgs.append(row_img)
                    row_data_imgs.append(row_imgs)
                    rune_data.append(row_imgs)
                row_imgs = []
                for row in rune_div_fragment.find_all("div", {"class": "fragment__row"}):
                    row_img = ["https:" + img["src"] for img in row.find_all("img")]
                    row_imgs.append(row_img)
                row_data_imgs.append(row_imgs)
                print(json.dumps(row_data_imgs, indent=4))

        return MessageItem(
            MessageChain.create([
                Image.fromUnsafeAddress(url) for url in skill_imgs
            ]),
            QuoteSource(GroupStrategy())
        )


# loop = asyncio.get_event_loop()
# loop.run_until_complete(LOLItemRaidersHandler.get_hero_statics("neeko", "mid"))
