import re
import aiohttp
import datetime

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.utils import MessageChainUtils
from SAGIRIBOT.MessageSender.Strategy import Normal
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount


class BiliBiliBangumiScheduleHandler(AbstractHandler):
    __name__ = "BiliBiliBangumiScheduleHandler"
    __description__ = "一个可以获取BiliBili7日内新番时间表的Handler"
    __usage__ = "在群内发送 `[1-7]日内新番` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if re.match(r"[1-7]日内新番", message.asDisplay()):
            await update_user_call_count_plus1(group, member, UserCalledCount.search, "search")
            days = int(message.asDisplay()[0])
            set_result(message, await self.formatted_output_bangumi(group, member, days))
        else:
            return None

    @staticmethod
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
            "accept-encoding": "gzip, deflate",
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

    @staticmethod
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
        all_bangumi_data = await BiliBiliBangumiScheduleHandler.get_new_bangumi_json()
        all_bangumi_data = all_bangumi_data["result"][-7:]
        formatted_bangumi_data = list()

        for bangumi_data in all_bangumi_data:
            temp_bangumi_data_list = list()
            for data in bangumi_data["seasons"]:
                temp_bangumi_data_dict = dict()
                temp_bangumi_data_dict["title"] = data["title"]
                temp_bangumi_data_dict["cover"] = data["cover"]
                temp_bangumi_data_dict["pub_index"] = data["delay_index"] + " (本周停更)" if data["delay"] else data["pub_index"]
                temp_bangumi_data_dict["pub_time"] = data["pub_time"]
                temp_bangumi_data_dict["url"] = data["url"]
                temp_bangumi_data_list.append(temp_bangumi_data_dict)
            formatted_bangumi_data.append(temp_bangumi_data_list)

        return formatted_bangumi_data

    @staticmethod
    @frequency_limit_require_weight_free(2)
    async def formatted_output_bangumi(group: Group, member: Member, days: int) -> MessageItem:
        """
        Formatted output json data

        Args:
            days: The number of days to output(1-7)

        Examples:
            data_str = formatted_output_bangumi(7)

        Return:
            MessageChain
        """
        formatted_bangumi_data = await BiliBiliBangumiScheduleHandler.get_formatted_new_bangumi_json()
        temp_output_substring = ["------BANGUMI------\n\n"]
        now = datetime.datetime.now()
        for index in range(days):
            temp_output_substring.append(now.strftime("%m-%d"))
            temp_output_substring.append("即将播出：")
            for data in formatted_bangumi_data[index]:
                temp_output_substring.append("\n%s %s %s\n" % (data["pub_time"], data["title"], data["pub_index"]))
            temp_output_substring.append("\n\n----------------\n\n")
            now += datetime.timedelta(days=1)

        content = "".join(temp_output_substring)
        return MessageItem(
            await MessageChainUtils.messagechain_to_img(MessageChain.create([Plain(text=content)])),
            Normal(GroupStrategy())
        )
