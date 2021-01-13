import aiohttp
from bs4 import BeautifulSoup

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain


async def get_almanac() -> list:
    url = "https://laohuangli.bmcx.com/"
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as resp:
            html = await resp.read()
    soup = BeautifulSoup(html, "html.parser")
    target_trs = soup.find_all("table")[3].find_all("tr")
    # print(target_trs)
    data = {}
    for i in target_trs:
        tds = i.find_all("td")
        key = tds[0].get_text().strip()
        value = tds[1].get_text().strip()
        data[key] = value

    text = f"今天是{data['日期']}\n宜：{data['宜'].replace('.', '、')}\n忌：{data['忌'].replace('.', '、')}"

    return [
        "None",
        MessageChain.create([
            Plain(text=text)
        ])
    ]
    # print(tr)
