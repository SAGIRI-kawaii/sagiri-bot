# -*- coding: utf-8 -*-
import aiohttp
import datetime
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.tools import text2piiic
from SAGIRIBOT.basics.tools import count_len
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting


async def get_new_bangumi_json() -> dict:
    """
    Get json data from bilibili

    Args:

    Examples:
        data = await get_new_bangumi_json()

    Return:
        dict:data get from bilibili
    """
    url = "https://bangumi.bilibili.com/web_api/timeline_global"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "origin": "https://www.bilibili.com",
        "referer": "https://www.bilibili.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers) as resp:
            result = await resp.json()
    return result


async def get_formatted_new_bangumi_json() -> list:
    """
    Format the json data

    Args:

    Examples:
        data = get_formatted_new_bangumi_json()

    Returns:
        {
            "title": str,
            "cover": str,
            "pub_index": str,
            "pub_time": str,
            "url": str
        }
    """
    all_bangumi_data = await get_new_bangumi_json()
    all_bangumi_data = all_bangumi_data["result"][-7:]
    formatted_bangumi_data = list()

    for bangumi_data in all_bangumi_data:
        temp_bangumi_data_list = list()
        for data in bangumi_data["seasons"]:
            temp_bangumi_data_dict = dict()
            temp_bangumi_data_dict["title"] = data["title"]
            temp_bangumi_data_dict["cover"] = data["cover"]
            temp_bangumi_data_dict["pub_index"] = data["pub_index"]
            temp_bangumi_data_dict["pub_time"] = data["pub_time"]
            temp_bangumi_data_dict["url"] = data["url"]
            temp_bangumi_data_list.append(temp_bangumi_data_dict)
        formatted_bangumi_data.append(temp_bangumi_data_list)

    return formatted_bangumi_data


async def formatted_output_bangumi(days: int, group_id: int) -> list:
    """
    Formatted output json data

    Args:
        days: The number of days to output(1-7)
        group_id: Group id

    Examples:
        data_str = formatted_output_bangumi(7)

    Return:
        str: formatted
    """
    formatted_bangumi_data = await get_formatted_new_bangumi_json()
    temp_output_substring = ["------BANGUMI------\n\n"]
    now = datetime.datetime.now()
    for index in range(days):
        temp_output_substring.append(now.strftime("%m-%d"))
        temp_output_substring.append("即将播出：")
        for data in formatted_bangumi_data[index]:
            temp_output_substring.append("\n%s %s %s\n" % (data["pub_time"], data["title"], data["pub_index"]))
            # temp_output_substring.append("url:%s\n" % (data["url"]))
        temp_output_substring.append("\n\n----------------\n\n")
        now += datetime.timedelta(days=1)

    long_text_setting = await get_setting(group_id, "longTextType")
    content = "".join(temp_output_substring)
    if long_text_setting == "img":
        img = text2piiic(string=content, poster="", length=int(max(count_len(line) for line in content.split("\n")) / 2))
        img.save("./statics/temp/tempBungumiTimeTable.png")
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile("./statics/temp/tempBungumiTimeTable.png")
            ])
        ]
    elif long_text_setting == "text":
        return [
            "None",
            MessageChain.create([
                Plain(text=content)
            ])
        ]
    else:
        return [
            "None",
            MessageChain.create([
                Plain(text="数据库 longTextType 项出错！请检查！")
            ])
        ]
