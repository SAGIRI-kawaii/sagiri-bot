import aiohttp

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.tools import text2piiic
from SAGIRIBOT.basics.tools import messagechain_to_img
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting
from SAGIRIBOT.basics.tools import count_len


async def get_abbreviation_explain(abbreviation: str, group_id: int) -> list:
    url = "https://lab.magiconch.com/api/nbnhhsh/guess"
    headers = {
        "referer": "https://lab.magiconch.com/nbnhhsh/"
    }
    data = {
        "text": abbreviation
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=data) as resp:
            res = await resp.json()
    # print(res)
    result = "可能的结果:\n\n"
    has_result = False
    for i in res:
        if "trans" in i:
            if i["trans"]:
                has_result = True
                result += f"{i['name']} => {'，'.join(i['trans'])}\n\n"
            else:
                result += f"{i['name']} => 没找到结果！\n\n"
        else:
            if i["inputting"]:
                has_result = True
                result += f"{i['name']} => {'，'.join(i['inputting'])}\n\n"
            else:
                result += f"{i['name']} => 没找到结果！\n\n"

    long_text_setting = await get_setting(group_id, "longTextType")
    if has_result:
        if long_text_setting == "img":
            # img = text2piiic(string=result, poster="", length=int(max(count_len(line) for line in result.split("\n")) / 2))
            # img.save("./statics/temp/tempAbbreviation.png")
            msg = await messagechain_to_img(MessageChain.create([
                    Plain(text=result)
                ]), save_path="./statics/temp/tempAbbreviation.png")
            return [
                "quoteSource",
                msg
            ]
        elif long_text_setting == "text":
            return [
                "quoteSource",
                MessageChain.create([
                    Plain(text=result)
                ])
            ]
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="数据库 longTextType 项出错！请检查！")
                ])
            ]
    else:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="没有找到结果哦~")
            ])
        ]
