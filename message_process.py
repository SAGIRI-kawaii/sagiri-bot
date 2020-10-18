from graia.application.event.messages import *

from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import Image

from functions.images.get_image import get_pic
from functions.crawer.weibo.weibo_crawer import get_weibo_hot
from functions.crawer.bilibili.bangumi_crawer import formatted_output_bangumi
from functions.crawer.leetcode.leetcode_user_info_crawer import get_leetcode_statics
from functions.crawer.steam.steam_game_info_crawer import get_steam_game_search
from functions.data_manage.get_data.get_setting import get_setting
from functions.data_manage.update_data.set_get_image_ready import set_get_img_ready
from functions.data_manage.get_data.get_image_ready import get_image_ready
from functions.crawer.saucenao.search_image import search_image
from functions.images.image_yellow_judge import image_yellow_judge
from functions.data_manage.update_data.update_dragon import update_dragon_data
from functions.images.get_wallpaper_time import get_wallpaper_time


async def group_message_process(
        message: MessageChain,
        message_info: GroupMessage
) -> list:
    """
    Process the received message and return the corresponding message

    Args:
        message: Received message(MessageChain)
        message_info: Received message(GroupMessage)

    Examples:
        message_list = await message_process(message, message_info)

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    message_text = message.asDisplay()
    sender = message_info.sender.id
    group_id = message_info.sender.group.id

    """
    图片功能：
        setu
        real
        bizhi
        time
        search
        yellow predict
    """
    if message_text == "setu":
        if await get_setting(group_id, "setu"):
            await update_dragon_data(group_id, sender, "normal")
            return await get_pic("setu")
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="我们是正规群呐，不搞那一套哦，想看去辣种群看哟~")
                ])
            ]

    elif message_text == "real":
        if await get_setting(group_id, "real"):
            return await get_pic("real")
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="我们是正规群呐，不搞那一套哦，想看去辣种群看哟~")
                ])
            ]

    elif message_text == "bizhi":
        if await get_setting(group_id, "bizhi"):
            return await get_pic("bizhi")
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="壁纸功能关闭了呐~想要打开的话就联系管理员吧~")
                ])
            ]
    elif message_text == "几点了":
        return await get_wallpaper_time(group_id, sender)

    elif message_text == "搜图":
        if await get_setting(group_id, "search"):
            res = await set_get_img_ready(group_id, sender, True, "searchReady")
            # print("res:", res)
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
    elif message.has(Image) and await get_setting(group_id, "search") and await get_image_ready(group_id, sender, "searchReady"):
        image = message.get(Image)[0]
        return await search_image(group_id, sender, image)

    elif message_text == "这张图涩吗":
        if not await get_setting(group_id,"yellowPredict"):
            return [
                "None",
                MessageChain.create([
                    At(target=sender),
                    Plain(text="图片涩度评价功能关闭了呐~想要打开就联系机器人管理员吧~")
                ])
            ]
        else:
            await set_get_img_ready(group_id, sender, True, "yellowPredictReady")
            return [
                "None",
                MessageChain.create([
                    At(target=sender),
                    Plain(text="请发送要预测的图片呐~")
                ])
            ]
    elif message.has(Image) and await get_setting(group_id, "yellowPredict") and await get_image_ready(group_id, sender, "yellowPredictReady"):
        image = message.get(Image)[0]
        return await image_yellow_judge(group_id, sender, image, "yellowPredict")

    # 爬虫相关功能
    """
    SAGIRI API相关功能：
        历史上的今天
        
    """
    """
    微博相关功能：
        微博热搜
    """
    if message_text == "weibo" or message_text == "微博":
        return await get_weibo_hot()

    """
    B站相关功能:
        B站新番时间表
        B站直播间查询
    """
    if message_text[-4:] == "日内新番":
        num = message_text[:-4]
        if not num.isdigit() or int(num) <= 0 or int(num) > 7:
            return [
                At(target=sender),
                Plain(text="参数错误！必须为数字1-7！")
            ]
        else:
            return await formatted_output_bangumi(int(num))

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
        return await get_steam_game_search(message_text.replace("steam ", ""))
    return ["None"]
