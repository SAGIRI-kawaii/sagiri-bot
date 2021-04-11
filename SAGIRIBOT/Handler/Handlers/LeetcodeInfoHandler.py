import re
import json
import aiohttp

from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount


class LeetcodeInfoHanlder(AbstractHandler):
    __name__ = "LeetcodeInfoHanlder"
    __description__ = "一个可以获取Leetcode信息的Handler"
    __usage__ = "在群中发送 `leetcode userslug` 即可（userslug为个人主页地址最后的唯一识别代码）"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        self.group = group
        self.member = member
        message_text = message.asDisplay()
        if re.match(r"leetcode \S+", message_text):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return await self.leetcode_user_info_crawer(message)
        elif re.match(r"(leetcode|力扣)每日一题", message_text):
            pass
        else:
            return await super().handle(app, message, group, member)

    @staticmethod
    async def leetcode_user_info_crawer(message: MessageChain) -> MessageItem:
        user_slug = message.asDisplay()[9:]
        return await LeetcodeInfoHanlder.get_leetcode_user_statics(user_slug)

    @staticmethod
    async def get_leetcode_user_statics(account_name: str) -> MessageItem:
        url = "https://leetcode-cn.com/graphql/"
        headers = {
            "origin": "https://leetcode-cn.com",
            "referer": "https://leetcode-cn.com/u/%s/" % account_name,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/80.0.3987.100 Safari/537.36",
            "x-definition-name": "userProfilePublicProfile",
            "x-operation-name": "userPublicProfile",
            "content-type": "application/json"
        }
        payload = {
            'operationName': "userPublicProfile",
            "query":
                "query userPublicProfile($userSlug: String!) {\n  userProfilePublicProfile(userSlug: $userSlug) {\n  "
                 "  username,\n    haveFollowed,\n    siteRanking,\n    profile {\n      userSlug,\n      realName,"
                 "\n      aboutMe,\n      userAvatar,\n      location,\n      gender,\n      websites,"
                 "\n      skillTags,\n      contestCount,\n      asciiCode,\n      medals {\n        name,"
                 "\n        year,\n        month,\n        category,\n        __typename,\n      }\n      ranking {\n "
                 "       rating,\n        ranking,\n        currentLocalRanking,\n        currentGlobalRanking,"
                 "\n        currentRating,\n        ratingProgress,\n        totalLocalUsers,\n        "
                 "totalGlobalUsers,\n        __typename,\n      }\n      skillSet {\n        langLevels {\n          "
                 "langName,\n          langVerboseName,\n          level,\n          __typename,\n        }\n        "
                 "topics {\n          slug,\n          name,\n          translatedName,\n          __typename,"
                 "\n        }\n        topicAreaScores {\n          score,\n          topicArea {\n            name,"
                 "\n            slug,\n            __typename,\n          }\n          __typename,\n        }\n       "
                 " __typename,\n      }\n      socialAccounts {\n        provider,\n        profileUrl,"
                 "\n        __typename,\n      }\n      __typename,\n    }\n    educationRecordList {\n      "
                 "unverifiedOrganizationName,\n      __typename,\n    }\n    occupationRecordList {\n      "
                 "unverifiedOrganizationName,\n      jobTitle,\n      __typename,\n    }\n    submissionProgress {\n  "
                 "    totalSubmissions,\n      waSubmissions,\n      acSubmissions,\n      reSubmissions,"
                 "\n      otherSubmissions,\n      acTotal,\n      questionTotal,\n      __typename\n    }\n    "
                 "__typename\n  }\n}",
            'variables': '{"userSlug": "%s"}' % account_name
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=json.dumps(payload)) as resp:
                data_json = await resp.json()

        if 'userProfilePublicProfile' in data_json["data"].keys() and data_json["data"]['userProfilePublicProfile'] is None:
            return MessageItem(MessageChain.create([Plain(text=f"未找到 userSlug: {account_name}!")]), Normal(GroupStrategy()))
        data_json = data_json['data']['userProfilePublicProfile']
        profile = data_json['profile']

        user_slug = profile['userSlug']

        user_name = profile['realName']

        ranking = data_json['siteRanking']
        if ranking == 100000:
            ranking = "%s+" % ranking

        websites_list = profile['websites']
        websites = []
        for i in websites_list:
            websites.append("\n    %s" % i)

        skills_list = profile['skillTags']
        skills = []
        for i in skills_list:
            skills.append("\n    %s" % i)

        architecture = profile['skillSet']['topicAreaScores'][0]['score']
        data_structures = profile['skillSet']['topicAreaScores'][1]['score']
        algorithms = profile['skillSet']['topicAreaScores'][2]['score']
        design = profile['skillSet']['topicAreaScores'][3]['score']
        solved_problems = data_json['submissionProgress']['acTotal']
        ac_submissions = data_json['submissionProgress']['acSubmissions']
        total_question = data_json['submissionProgress']['questionTotal']
        total_submissions = data_json['submissionProgress']['totalSubmissions']
        submission_pass_rate = float(100 * ac_submissions / total_submissions)

        text = """userSlug: %s
    userName: %s
    ranking: %s
    websites: %s
    skills: %s
    score:
        architecture: %s%%
        data-structures: %s%%
        algorithms: %s%%
        design: %s%%
    solvedProblems: %s/%s
    acSubmissions: %s
    submissionPassRate:%.2f%%
        """ % (user_slug,
               user_name,
               ranking,
               "".join(websites),
               "".join(skills),
               architecture,
               data_structures,
               algorithms,
               design,
               solved_problems,
               total_question,
               ac_submissions,
               submission_pass_rate
               )
        return MessageItem(MessageChain.create([Plain(text=text)]), Normal(GroupStrategy()))
