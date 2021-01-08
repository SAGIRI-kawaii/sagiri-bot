import re
import os
import pkuseg
import threading

from graia.application.event.messages import *
from graia.application import GraiaMiraiApplication

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Source

from SAGIRIBOT.images.get_image import get_pic
from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.crawer.weibo.weibo_crawer import get_weibo_hot
from SAGIRIBOT.crawer.bilibili.bangumi_crawer import formatted_output_bangumi
from SAGIRIBOT.crawer.leetcode.leetcode_user_info_crawer import get_leetcode_statics
from SAGIRIBOT.crawer.steam.steam_game_info_crawer import get_steam_game_search
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting
from SAGIRIBOT.data_manage.update_data.set_get_image_ready import set_get_img_ready
from SAGIRIBOT.data_manage.get_data.get_image_ready import get_image_ready
from SAGIRIBOT.crawer.saucenao.search_image import search_image
from SAGIRIBOT.images.image_yellow_judge import image_yellow_judge
from SAGIRIBOT.crawer.tracemoe.search_bangumi import search_bangumi
from SAGIRIBOT.data_manage.update_data.update_dragon import update_dragon_data
from SAGIRIBOT.images.get_wallpaper_time import get_wallpaper_time
from SAGIRIBOT.images.get_wallpaper_time import show_clock_wallpaper
from SAGIRIBOT.functions.get_translate import get_translate
from SAGIRIBOT.data_manage.update_data.update_user_called_data import update_user_called_data
from SAGIRIBOT.functions.order_music import get_song_ordered
from SAGIRIBOT.functions.get_history_today import get_history_today
from SAGIRIBOT.process.setting_process import setting_process
from SAGIRIBOT.process.reply_process import reply_process
from SAGIRIBOT.crawer.bangumi.get_bangumi_info import get_bangumi_info
from SAGIRIBOT.data_manage.get_data.get_admin import get_admin
from SAGIRIBOT.data_manage.get_data.get_blacklist import get_blacklist
from SAGIRIBOT.data_manage.get_data.get_rank import get_rank
from SAGIRIBOT.basics.write_log import write_log
from SAGIRIBOT.functions.get_joke import *
from SAGIRIBOT.functions.get_group_quotes import get_group_quotes
from SAGIRIBOT.functions.get_jlu_csw_notice import get_jlu_csw_notice
from SAGIRIBOT.basics.get_response_set import get_response_set
from SAGIRIBOT.images.get_setu_keyword import get_setu_keyword
from SAGIRIBOT.functions.petpet import petpet
from SAGIRIBOT.functions.pornhub_style_image import make_ph_style_logo
from SAGIRIBOT.functions.get_abbreviation_explain import get_abbreviation_explain
from SAGIRIBOT.functions.search_magnet import search_magnet
from SAGIRIBOT.data_manage.update_data.write_chat_record import write_chat_record
from SAGIRIBOT.functions.get_review import *
from SAGIRIBOT.basics.frequency_limit_module import GlobalFrequencyLimitDict

# 关键词字典
response_set = get_response_set()

seg = pkuseg.pkuseg()


async def limit_exceeded_judge(group_id: int, weight: int) -> list:
    frequency_limit_instance = GlobalFrequencyLimitDict()
    frequency_limit_instance.update(group_id, weight)
    if frequency_limit_instance.get(group_id) >= 10:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="Frequency limit exceeded every 10 seconds!")
            ])
        ]
    else:
        return []


async def group_message_process(
        message: MessageChain,
        message_info: GroupMessage,
        app: GraiaMiraiApplication,
        frequency_limit_dict: dict
) -> list:
    """
    Process the received message and return the corresponding message

    Args:
        message: Received message(MessageChain)
        message_info: Received message(GroupMessage)
        app: APP
        frequency_limit_dict: Frequency limit dict

    Examples:
        message_list = await message_process(message, message_info)

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    # print("debug")
    message_text = message.asDisplay()
    message_serialization = message.asSerializationString()
    sender = message_info.sender.id
    group_id = message_info.sender.group.id

    # 黑名单检测
    if sender in await get_blacklist():
        print("Blacklist!No reply!")
        return ["None"]
    await write_chat_record(seg, group_id, sender, message_text)

    # print("message_serialization:", message_serialization)

    if message.has(At) and message.get(At)[0].target == await get_config("BotQQ"):
        await update_user_called_data(group_id, sender, "at", 1)

    if message.has(At) and message.get(At)[0].target == await get_config("BotQQ") and re.search("@.* setting.*",
                                                                                                message_text):
        try:
            _, config, new_value = message_text.split(".")
            return await setting_process(group_id, sender, config, new_value)
        except ValueError:
            return [
                "None",
                MessageChain.create([
                    Plain(text="Command Error!")
                ])
            ]

    """
    图片功能：
        setu
        real
        bizhi
        time
        search
        yellow predict
        lsp rank
    """
    if message_text in response_set["setu"]:

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "setu"):
            if sender == 80000000:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="要涩图就光明正大！匿名算什么好汉！")
                    ])
                ]
            await update_dragon_data(group_id, sender, "normal")
            await update_user_called_data(group_id, sender, "setu", 1)
            if await get_setting(group_id, "r18"):
                return await get_pic("setu18", group_id, sender)
            else:
                return await get_pic("setu", group_id, sender)
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="我们是正规群呐，不搞那一套哦，想看去辣种群看哟~")
                ])
            ]

    elif re.search("来点.*[色涩]图", message_text):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "setu"):
            if sender == 80000000:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="要涩图就光明正大！匿名算什么好汉！")
                    ])
                ]
            keyword = re.findall("来点(.*?)[涩色]图", message_text, re.S)[0]
            print(keyword)
            if keyword in ["r18", "R18", "r-18", "R-18"]:
                return [
                    "quoteSource",
                    MessageChain.create([
                        Plain(text="此功能暂时还不支持搜索R18涩图呐~忍忍吧LSP！")
                    ])
                ]
            # await app.sendGroupMessage(

            await update_dragon_data(group_id, sender, "normal")
            await update_user_called_data(group_id, sender, "setu", 1)
            return await get_setu_keyword(keyword=keyword)
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="我们是正规群呐，不搞那一套哦，想看去辣种群看哟~")
                ])
            ]

    elif message_text in response_set["real"]:

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "real"):
            if sender == 80000000:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="要涩图就光明正大！匿名算什么好汉！")
                    ])
                ]
            await update_dragon_data(group_id, sender, "normal")
            await update_user_called_data(group_id, sender, "real", 1)
            return await get_pic("real", group_id, sender)
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="我们是正规群呐，不搞那一套哦，想看去辣种群看哟~")
                ])
            ]

    elif message_text in response_set["realHighq"]:

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "real"):
            if sender == 80000000:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="要涩图就光明正大！匿名算什么好汉！")
                    ])
                ]
            await update_dragon_data(group_id, sender, "normal")
            await update_user_called_data(group_id, sender, "real", 1)
            return await get_pic("realHighq", group_id, sender)
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="我们是正规群呐，不搞那一套哦，想看去辣种群看哟~")
                ])
            ]

    elif message_text in response_set["bizhi"]:

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "bizhi"):
            if sender == 80000000:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="要涩图就光明正大！匿名算什么好汉！")
                    ])
                ]
            await update_user_called_data(group_id, sender, "bizhi", 1)
            return await get_pic("bizhi", group_id, sender)
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="壁纸功能关闭了呐~想要打开的话就联系管理员吧~")
                ])
            ]

    elif message_text.startswith("setu*") or message_text.startswith("real*") or message_text.startswith("bizhi*"):
        if message_text.startswith("bizhi*"):
            command = "bizhi"
            num = message_text[6:]
        else:
            command = message_text[:4]
            num = message_text[5:]
        if num.isdigit():
            num = int(num)
            if sender not in await get_admin(group_id):
                if 0 <= num <= 5:
                    return [
                        "None",
                        MessageChain.create([
                            Plain(text="只有主人和管理员可以使用%s*num命令哦~你没有权限的呐~" % command)
                        ])
                    ]
                elif num < 0:
                    return [
                        "None",
                        MessageChain.create([
                            Plain(text="%d？你有问题？不如给爷吐出%d张来" % (num, -num))
                        ])
                    ]
                else:
                    return [
                        "None",
                        MessageChain.create([
                            Plain(text="不是管理员你要你🐎呢？老色批！还要那么多？给你🐎一拳，给爷爬！")
                        ])
                    ]
            if num < 0:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="%d？你有问题？不如给爷吐出%d张来" % (num, -num))
                    ])
                ]
            elif num > 5:
                if sender == await get_config("HostQQ"):
                    return ["%s*" % command, num]
                else:
                    return [
                        "None",
                        MessageChain.create([
                            Plain(text="管理最多也只能要5张呐~我可不会被轻易玩儿坏呢！！！！")
                        ])
                    ]
            else:
                if sender != await get_config("HostQQ"):
                    await update_user_called_data(group_id, sender, command, num)
                return ["%s*" % command, int(num)]
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="必须为数字！")
                ])
            ]

    elif message_text == "几点了":
        return await get_wallpaper_time(group_id, sender)

    elif message_text.startswith("选择表盘"):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        if message_text == "选择表盘":
            return await show_clock_wallpaper(sender)

    elif message_text == "搜图":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 2)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "search"):
            await set_get_img_ready(group_id, sender, True, "searchReady")
            return [
                "None",
                MessageChain.create([
                    At(sender),
                    Plain(text="请发送要搜索的图片呐~(仅支持pixiv图片搜索呐！)")
                ])
            ]
        else:
            return [
                "None",
                MessageChain.create([
                    At(sender),
                    Plain(text="搜图功能关闭了呐~想要打开就联系管理员吧~")
                ])
            ]
    elif message.has(Image) and await get_setting(group_id, "search") and await get_image_ready(group_id, sender,
                                                                                                "searchReady"):
        # print("status:", await get_image_ready(group_id, sender, "searchReady"))
        image = message.get(Image)[0]
        await update_user_called_data(group_id, sender, "search", 1)
        return await search_image(group_id, sender, image)

    elif message_text == "这张图涩吗":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 2)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "yellowPredict"):
            await set_get_img_ready(group_id, sender, True, "yellowPredictReady")
            return [
                "None",
                MessageChain.create([
                    At(target=sender),
                    Plain(text="请发送要预测的图片呐~")
                ])
            ]
        else:
            return [
                "None",
                MessageChain.create([
                    At(target=sender),
                    Plain(text="图片涩度评价功能关闭了呐~想要打开就联系机器人管理员吧~")
                ])
            ]
    elif message.has(Image) and await get_setting(group_id, "yellowPredict") and await get_image_ready(group_id, sender,
                                                                                                       "yellowPredictReady"):
        image = message.get(Image)[0]
        await update_user_called_data(group_id, sender, "yellowPredict", 1)
        return await image_yellow_judge(group_id, sender, image, "yellowPredict")

    elif message_text == "搜番":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 2)
            if frequency_limit_res:
                return frequency_limit_res

        if await get_setting(group_id, "searchBangumi"):
            await set_get_img_ready(group_id, sender, True, "searchBangumiReady")
            return [
                "None",
                MessageChain.create([
                    At(sender),
                    Plain(text="请发送要搜索的图片呐~(仅支持番剧图片搜索呐！)")
                ])
            ]
        else:
            return [
                "None",
                MessageChain.create([
                    At(sender),
                    Plain(text="搜番功能关闭了呐~想要打开就联系管理员吧~")
                ])
            ]
    elif message.has(Image) and await get_setting(group_id, "searchBangumi") and await get_image_ready(group_id, sender,
                                                                                                       "searchBangumiReady"):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 2)
            if frequency_limit_res:
                return frequency_limit_res

        # print("status:", await get_image_ready(group_id, sender, "searchReady"))
        image = message.get(Image)[0]
        await update_user_called_data(group_id, sender, "search", 1)
        return await search_bangumi(group_id, sender, image.url)

    elif message_text == "rank":
        return await get_rank(group_id, app)

    # 爬虫相关功能
    """
    SAGIRI API相关功能：
        历史上的今天
    """
    if message_text == "历史上的今天":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        return await get_history_today()
    """
    微博相关功能：
        微博热搜
    """
    if message_text == "weibo" or message_text == "微博":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        return await get_weibo_hot(group_id)

    """
    B站相关功能:
        B站新番时间表
        B站直播间查询
    """
    if message_text[-4:] == "日内新番":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        num = message_text[:-4]
        if not num.isdigit() or int(num) <= 0 or int(num) > 7:
            return [
                At(target=sender),
                Plain(text="参数错误！必须为数字1-7！")
            ]
        else:
            return await formatted_output_bangumi(int(num), group_id)

    """
    力扣相关功能：
        用户信息查询
        每日一题查询
        具体题目查询
    """
    if message_text.startswith("leetcode "):
        return await get_leetcode_statics(message_text.replace("leetcode ", ""))

    """
    steam相关功能：
        steam游戏查询
    """
    if message_text.startswith("steam "):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 2)
            if frequency_limit_res:
                return frequency_limit_res

        return await get_steam_game_search(message_text.replace("steam ", ""))

    """
    bangumi相关功能：
        番剧查询
    """
    if message_text.startswith("番剧 "):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 2)
            if frequency_limit_res:
                return frequency_limit_res

        keyword = message_text[3:]
        return await get_bangumi_info(sender, keyword)

    """
    其他功能:
        文本翻译
        点歌
        机器人帮助
        自动回复
        笑话
        群语录
        平安经（群人数过多时慎用）
        pornhub风格图片生成
        缩写
        获取磁力链
        年度报告
        摸~
    """
    if message.has(At) and message.get(At)[0].target == await get_config("BotQQ") and re.search(".*用.*怎么说",
                                                                                                message_text):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        return await get_translate(message_text, sender)

    elif message_text.startswith("点歌 ") and len(message_text) >= 4:

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 3)
            if frequency_limit_res:
                return frequency_limit_res

        print("search song:", message_text[3:])
        return await get_song_ordered(message_text[3:])

    if message_text == "help" or message_text == "!help" or message_text == "/help" or message_text == "！help":
        return [
            "None",
            MessageChain.create([
                Plain(text="点击链接查看帮助：http://doc.sagiri-web.com/web/#/p/c79d523043f6ec05c1ac1416885477c7\n"),
                Plain(text="文档尚未完善，功能说明还在陆续增加中！")
            ])
        ]

    if message_text == "教务通知":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        return await get_jlu_csw_notice(group_id)

    if re.search("来点.*笑话", message_text):
        joke_dict = {
            "苏联": "soviet",
            "法国": "french",
            "法兰西": "french",
            "美国": "america",
            "美利坚": "america"
        }
        name = re.findall(r'来点(.*?)笑话', message_text, re.S)
        if name == ['']:
            return [
                "None",
                MessageChain.create([
                    At(target=sender),
                    Plain(text="来点儿啥笑话啊，你又不告诉人家！哼！")
                ])
            ]
        elif name[0] in joke_dict.keys():
            msg = await get_key_joke(joke_dict[name[0]])
            await write_log("joke", "none", sender, group_id, True, "function")
            return msg
        else:
            msg = await get_joke(name[0])
            await write_log("joke", "none", sender, group_id, True, "function")
            return msg

    if message_text == "群语录":
        return await get_group_quotes(group_id, app, "None", "random", "None")
    elif re.search("来点.*语录", message_text):
        name = re.findall(r'来点(.*?)语录', message_text, re.S)[0]
        at_obj = message.get(At)
        if name == [] and at_obj == []:
            return ["None"]
        elif at_obj:
            at_str = at_obj[0].asSerializationString()
            member_id = re.findall(r'\[mirai:at:(.*?),@.*?\]', at_str, re.S)[0]
            await write_log("quotes", "None", sender, group_id, True, "function")
            if message_text[-4:] == ".all":
                return await get_group_quotes(group_id, app, member_id, "all", "memberId")
            else:
                return await get_group_quotes(group_id, app, member_id, "select", "memberId")
        elif name:
            await write_log("quotes", "None", sender, group_id, True, "function")
            if message_text[-4:] == ".all":
                return await get_group_quotes(group_id, app, name, "all", "nickname")
            else:
                return await get_group_quotes(group_id, app, name, "select", "nickname")

    if message_text == "平安":

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 6)
            if frequency_limit_res:
                return frequency_limit_res

        member_list = await app.memberList(group_id)
        msg = list()
        msg.append(Plain(text=f"群{message_info.sender.group.name}平安经\n"))
        for i in member_list:
            msg.append(Plain(text=f"{i.name}平安\n"))
        return [
            "None",
            MessageChain.create(msg)
        ]

    if message_text.startswith("ph ") and len(message_text.split(" ")) == 3:

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        if "\\" in message_text or "/" in message_text:
            return [
                "None",
                MessageChain.create([
                    Plain(text="不支持 '/' 与 '\\' ！")
                ])
            ]
        args = message_text.split(" ")
        left_text = args[1]
        right_text = args[2]
        path = f'./statics/temp/ph_{left_text}_{right_text}.png'
        if not os.path.exists(path):
            try:
                await make_ph_style_logo(left_text, right_text)
            except OSError as e:
                if "[Errno 22] Invalid argument:" in str(e):
                    return [
                        "quoteSource",
                        MessageChain.create([
                            Plain(text="非法字符！")
                        ])
                    ]
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile(path)
            ])
        ]

    # if message_text.startswith("缩 "):
    #     abbreviation = message_text[2:]
    #     print(abbreviation)
    #     if abbreviation.isalnum():
    #         return await get_abbreviation_explain(abbreviation, group_id)
    #     else:
    #         return [
    #             "quoteSource",
    #             MessageChain.create([
    #                 Plain(text="只能包含数字及字母！")
    #             ])
    #         ]

    if message_text.startswith("magnet "):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 6)
            if frequency_limit_res:
                return frequency_limit_res

        target = message_text[7:]
        return await search_magnet(target, group_id)

    if message_text == "我的年内总结":
        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 6)
            if frequency_limit_res:
                return frequency_limit_res

        return await get_personal_review(group_id, sender, "year")

    if message_text == "我的月内总结":
        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 6)
            if frequency_limit_res:
                return frequency_limit_res

        return await get_personal_review(group_id, sender, "month")

    if message_text == "本群年内总结" and sender == await get_config("HostQQ"):
        # lock = threading.Lock()
        # lock.acquire()
        msg = await get_group_review(group_id, sender, "year")
        # lock.release()
        return msg

    if message_text == "本群月内总结" and sender == await get_config("HostQQ"):
        # lock = threading.Lock()
        # lock.acquire()
        msg = await get_group_review(group_id, sender, "month")
        # lock.release()
        return msg

    if message.has(At) and message_text.startswith("摸") or message_text.startswith("摸 "):

        if await get_setting(group_id, "countLimit"):
            frequency_limit_res = await limit_exceeded_judge(group_id, 1)
            if frequency_limit_res:
                return frequency_limit_res

        target_id = message.get(At)[0].target
        await petpet(target_id)
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile(f'./statics/temp/tempPetPet-{target_id}.gif')
            ])
        ]

    if message.has(At) and message.get(At)[0].target == await get_config("BotQQ"):
        return await reply_process(group_id, sender, message_text)
    return ["None"]
