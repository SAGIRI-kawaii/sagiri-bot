import aiohttp
import random
from bs4 import BeautifulSoup

from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.chain import MessageChain

from SAGIRIBOT.basics.tools import text2piiic
from SAGIRIBOT.basics.tools import count_len
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting


async def get_github_hot(group_id: int) -> list:
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as resp:
            html = await resp.read()
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", {"class": "Box-row"})

    text_list = [f"随机数:{random.randint(0,10000)}", "\ngithub实时热榜:\n"]
    index = 0
    for i in articles:
        try:
            index += 1
            text_list.append("\n%d. %s\n" % (index, i.find("h1").get_text().replace("\n", "").replace(" ", "").replace("\\", " \\ ")))
            text_list.append("\n    %s\n" % i.find("p").get_text().strip())
        except Exception:
            pass

    text = "".join(text_list).replace("#", "")
    long_text_setting = await get_setting(group_id, "longTextType")
    if long_text_setting == "img":
        img = text2piiic(string=text, poster="", length=int(max(count_len(line) for line in text.split("\n")) / 2))
        img.save("./statics/temp/tempGithub.png")
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile("./statics/temp/tempGithub.png")
            ])
        ]
    elif long_text_setting == "text":
        return [
            "None",
            MessageChain.create([
                Plain(text=text)
            ])
        ]
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="数据库 longTextType 项出错！请检查！")
            ])
        ]