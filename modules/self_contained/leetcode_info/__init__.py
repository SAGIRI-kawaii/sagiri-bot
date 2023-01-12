import json
import aiohttp

from graia.ariadne.message.element import Plain, Image, Source
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult

from shared.utils.text2img import html2img
from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)


channel = Channel.current()
channel.name("LeetcodeInfo")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个可以获取Leetcode信息的插件\n"
    "在群中发送 `leetcode userslug` 可查询个人资料（userslug为个人主页地址最后的唯一识别代码）\n"
    "在群中发送 `leetcode每日一题` 可查询每日一题"
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch("每日一题$", optional=True) @ "daily_question",
                RegexMatch(r"\S+", optional=True) @ "user_slug",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("leetcode_info", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def leetcode_info(app: Ariadne, group: Group, daily_question: RegexResult, user_slug: RegexResult):
    if not daily_question.matched and not user_slug.matched or daily_question.matched and user_slug.matched:
        return
    if daily_question.matched:
        await app.send_group_message(group, await get_leetcode_daily_question())
    else:
        await app.send_group_message(group, await get_leetcode_user_statics(user_slug.result.display))


async def get_daily_question_json():
    url = "https://leetcode.cn/graphql/"
    headers = {
        "content-type": "application/json",
        "origin": "https://leetcode.cn",
        "referer": "https://leetcode.cn/problemset/all/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/84.0.4147.135 Safari/537.36 ",
    }
    payload = {
        "operationName": "questionOfToday",
        "variables": {},
        "query": "query questionOfToday {\n  todayRecord {\n    question {\n      questionFrontendId,"
        "\n      questionTitleSlug,\n      __typename\n    }\n    lastSubmission {\n      id,"
        "\n      __typename,\n    }\n    date,\n    userStatus,\n    __typename\n  }\n}\n ",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url, headers=headers, data=json.dumps(payload)
        ) as resp:
            result = await resp.json()
    return result


async def get_question_content(question_title_slug, language="Zh"):
    url = "https://leetcode.cn/graphql/"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "origin": "https://leetcode.cn",
        "referer": f"https://leetcode.cn/problems/{question_title_slug}/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/84.0.4147.135 Safari/537.36",
        "x-definition-name": "question",
        "x-operation-name": "questionData",
        "x-timezone": "Asia/Shanghai",
    }
    payload = {
        "operationName": "questionData",
        "variables": {"titleSlug": question_title_slug},
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
        "dailyRecordStatus\n    editorType\n    ugcQuestionId\n    style\n    __typename\n  }\n}\n ",
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


async def get_leetcode_daily_question(language: str = "Zh") -> MessageChain:
    if language != "Zh" and language != "En":
        raise ValueError("Language only can be Zh or En!")

    question_slug_data = await get_daily_question_json()
    question_slug = question_slug_data["data"]["todayRecord"][0]["question"][
        "questionTitleSlug"
    ]
    content = await get_question_content(question_slug, language)
    return MessageChain(Image(data_bytes=await html2img(content)))


async def get_leetcode_user_statics(account_name: str) -> MessageChain:
    url = "https://leetcode.cn/graphql/"
    headers = {
        "origin": "https://leetcode.cn",
        "referer": "https://leetcode.cn/u/%s/" % account_name,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/80.0.3987.100 Safari/537.36",
        "x-definition-name": "userProfilePublicProfile",
        "x-operation-name": "userPublicProfile",
        "content-type": "application/json",
    }
    payload = {
        "operationName": "userPublicProfile",
        "query": "query userPublicProfile($userSlug: String!) {\n  userProfilePublicProfile(userSlug: $userSlug) {\n  "
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
        "variables": '{"userSlug": "%s"}' % account_name,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url, headers=headers, data=json.dumps(payload)
        ) as resp:
            data_json = await resp.json()

    if (
        "userProfilePublicProfile" in data_json["data"].keys()
        and data_json["data"]["userProfilePublicProfile"] is None
    ):
        return MessageChain(f"未找到 userSlug: {account_name}!")
    data_json = data_json["data"]["userProfilePublicProfile"]
    profile = data_json["profile"]

    user_slug = profile["userSlug"]

    user_name = profile["realName"]

    ranking = data_json["siteRanking"]
    if ranking == 100000:
        ranking = "%s+" % ranking

    websites_list = profile["websites"]
    websites = ["\n    %s" % i for i in websites_list]
    skills_list = profile["skillTags"]
    skills = ["\n    %s" % i for i in skills_list]
    data_structures = profile["skillSet"]["topicAreaScores"][0]["score"]
    design = profile["skillSet"]["topicAreaScores"][1]["score"]
    architecture = profile["skillSet"]["topicAreaScores"][2]["score"]
    algorithms = profile["skillSet"]["topicAreaScores"][3]["score"]

    solved_problems = data_json["submissionProgress"]["acTotal"]
    ac_submissions = data_json["submissionProgress"]["acSubmissions"]
    total_question = data_json["submissionProgress"]["questionTotal"]
    total_submissions = data_json["submissionProgress"]["totalSubmissions"]
    submission_pass_rate = float(100 * ac_submissions / total_submissions)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=profile["userAvatar"]) as resp:
            img_content = await resp.read()
    return MessageChain([
        Image(data_bytes=img_content),
        Plain(text=f"\n站内标识: {user_slug}\n"),
        Plain(text=f"用户名: {user_name}\n"),
        Plain(text=f"站内排名: {ranking}\n"),
        Plain(text=f"技能:\n"),
        Plain(text=f"   基础架构: {architecture}%\n"),
        Plain(text=f"   数据结构: {data_structures}%\n"),
        Plain(text=f"   算法: {algorithms}%\n"),
        Plain(text=f"   设计: {design}%\n"),
        Plain(text=f"解题数量: {solved_problems}/{total_question}\n"),
        Plain(text=f"通过率: {submission_pass_rate}%"),
    ])
