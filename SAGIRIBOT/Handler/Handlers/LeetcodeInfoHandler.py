import re
import json
import aiohttp
from html import unescape

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage

from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.utils import update_user_call_count_plus1, UserCalledCount, MessageChainUtils

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def leetcode_info_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await LeetcodeInfoHanlder.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class LeetcodeInfoHanlder(AbstractHandler):
    __name__ = "LeetcodeInfoHanlder"
    __description__ = "一个可以获取Leetcode信息的Handler"
    __usage__ = "在群中发送 `leetcode userslug` 即可（userslug为个人主页地址最后的唯一识别代码）"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_text = message.asDisplay()
        if re.match(r"leetcode \S+", message_text):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return await LeetcodeInfoHanlder.leetcode_user_info_crawer(message)
        elif re.match(r"(leetcode|力扣)每日一题", message_text):
            await update_user_call_count_plus1(group, member, UserCalledCount.functions, "functions")
            return await LeetcodeInfoHanlder.get_leetcode_daily_question()
        else:
            return None

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

    @staticmethod
    async def get_daily_question_json():
        url = "https://leetcode-cn.com/graphql/"
        headers = {
            "content-type": "application/json",
            "origin": "https://leetcode-cn.com",
            "referer": "https://leetcode-cn.com/problemset/all/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
        }
        payload = {
            "operationName": "questionOfToday",
            "variables": {},
            "query": "query questionOfToday {\n  todayRecord {\n    question {\n      questionFrontendId,\n      questionTitleSlug,\n      __typename\n    }\n    lastSubmission {\n      id,\n      __typename,\n    }\n    date,\n    userStatus,\n    __typename\n  }\n}\n"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=json.dumps(payload)) as resp:
                result = await resp.json()
        return result

    @staticmethod
    async def get_question_content(questionTitleSlug, language="Zh"):
        url = "https://leetcode-cn.com/graphql/"
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "origin": "https://leetcode-cn.com",
            "referer": "https://leetcode-cn.com/problems/%s/" % questionTitleSlug,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
            "x-definition-name": "question",
            "x-operation-name": "questionData",
            "x-timezone": "Asia/Shanghai"
        }
        payload = {
            "operationName": "questionData",
            "variables": {"titleSlug": "%s" % questionTitleSlug},
            "query": "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    "
                     "questionId\n    questionFrontendId\n    boundTopicId\n    title\n    titleSlug\n    content\n   "
                     " translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    "
                     "dislikes\n    isLiked\n    similarQuestions\n    contributors {\n      username\n      "
                     "profileUrl\n      avatarUrl\n      __typename\n    }\n    langToValidPlayground\n    topicTags "
                     "{\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n "
                     "   codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n "
                     "   hints\n    solution {\n      id\n      canSeeDetail\n      __typename\n    }\n    status\n   "
                     " sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    "
                     "enableRunCode\n    envInfo\n    book {\n      id\n      bookName\n      pressName\n      "
                     "source\n      shortDescription\n      fullDescription\n      bookImgUrl\n      pressImgUrl\n    "
                     "  productUrl\n      __typename\n    }\n    isSubscribed\n    isDailyQuestion\n    "
                     "dailyRecordStatus\n    editorType\n    ugcQuestionId\n    style\n    __typename\n  }\n}\n "
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=json.dumps(payload)) as resp:
                result = await resp.json()
        if language == "En":
            return result["data"]["question"]["content"]
        elif language == "Zh":
            return result["data"]["question"]["translatedContent"]
        else:
            return None

    @staticmethod
    async def html_to_plain_text(html):
        text = re.sub('<head.*?>.*?</head>', '', html, flags=re.M | re.S | re.I)
        text = re.sub('<a\s.*?>', ' HYPERLINK ', text, flags=re.M | re.S | re.I)
        text = re.sub('<.*?>', '', text, flags=re.M | re.S)
        text = re.sub(r'(\s*\n)+', '\n', text, flags=re.M | re.S)
        return unescape(text)

    @staticmethod
    async def image_in_html_to_text(content):
        images = re.findall(r'<img.*?src="(.*?)".*?>', content, re.S)
        for i in range(len(images)):
            content = content.replace(images[i], "/>ImAgEiMaGe%dImAgE<img" % i)
        transformed = await LeetcodeInfoHanlder.html_to_plain_text(content)
        transformed = transformed.split("ImAgE")
        index = 0
        for i in range(len(transformed)):
            if "iMaGe" in transformed[i]:
                transformed[i] = "img[%d]:%s" % (index, images[index])
                index += 1
        return transformed

    @staticmethod
    async def get_leetcode_daily_question(language: str = "Zh") -> MessageItem:
        if language != "Zh" and language != "En":
            raise ValueError("Language only can be Zh or En!")

        question_slug_data = await LeetcodeInfoHanlder.get_daily_question_json()
        question_slug = question_slug_data["data"]["todayRecord"][0]["question"]["questionTitleSlug"]
        content = await LeetcodeInfoHanlder.get_question_content(question_slug, language)
        content = await LeetcodeInfoHanlder.image_in_html_to_text(content)
        message_list = []
        for i in content:
            if re.match(r"img\[[0-9]+]:", i):
                url = i.replace(re.findall(r"img\[[0-9]+]:", i, re.S)[0], '')
                async with aiohttp.ClientSession() as session:
                    async with session.post(url=url) as resp:
                        img_content = await resp.read()
                message_list.append(Image.fromUnsafeBytes(img_content))
            else:
                message_list.append(Plain(text=i))
        return MessageItem(
            await MessageChainUtils.messagechain_to_img(MessageChain.create(message_list)),
            Normal(GroupStrategy())
        )