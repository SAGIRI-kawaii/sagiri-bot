# -*- coding: utf-8 -*-
import asyncio
import os
from multiprocessing import Queue
import threading
import json
from aiohttp.client_exceptions import ClientResponseError
import traceback
import time

from graia.broadcast import Broadcast
from graia.scheduler import GraiaScheduler
from graia.scheduler import timers
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import App
from graia.application.message.elements.internal import Source
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.exceptions import *

from SAGIRIBOT.images.get_image import get_pic
from SAGIRIBOT.functions.get_dragon_king import get_dragon_king
from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.basics.bot_join_group_init import bot_join_group_init
from SAGIRIBOT.basics.check_group_data_init import check_group_data_init
from SAGIRIBOT.process.group_message_process import group_message_process
from SAGIRIBOT.process.friend_message_process import friend_message_process
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting
from SAGIRIBOT.data_manage.update_data.update_dragon import update_dragon_data
from SAGIRIBOT.basics.aio_mysql_excute import execute_sql
from SAGIRIBOT.basics.frequency_limit_module import frequency_limit
from SAGIRIBOT.basics.frequency_limit_module import GlobalFrequencyLimitDict
from SAGIRIBOT.basics.exception_resender import ExceptionReSender
from SAGIRIBOT.basics.exception_resender import exception_resender_listener
from SAGIRIBOT.functions.get_xml_image import get_xml_setu
from SAGIRIBOT.functions.get_group_announcement import get_group_announcement
from SAGIRIBOT.crawer.douban.get_new_books import get_douban_new_books


loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
sche = GraiaScheduler(loop=loop, broadcast=bcc)


with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    configs = json.loads(f.read())

app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=configs["miraiHost"],
        authKey=configs["authKey"],
        account=configs["BotQQ"],
        websocket=True
    )
)

# 复读判断
group_repeat = dict()
tasks = Queue()
lock = threading.Lock()
frequency_limit_dict = {}
frequency_limit_instance = None
exception_resender_instance = None

# async def group_message_sender(message_info: GroupMessage, message: list, group: Group,
#                                app: GraiaMiraiApplication) -> None:
#     message_send = await group_message_process(message, message_info, app)
#     await group_assist_process(message, message_info, message_send, group)


async def group_assist_process(received_message: MessageChain, message_info: GroupMessage, message: list,
                               group: Group, program_start) -> None:
    """
    Complete the auxiliary work that the function: message_process has not completed

    Args:
        received_message: Received message
        message: message list([what_needs_to_be_done, message_to_be_send])
        message_info: Message information
        group: Group class from the receive message
        program_start: process start time

    Examples:
        await group_assist_process(message, message_send, group)

    Return:
        None
    """

    global exception_resender_instance
    try:
        if len(message) > 1 and "*" not in message[0]:
            # lock.acquire()
            group_repeat[group.id]["lastMsg"] = group_repeat[group.id]["thisMsg"]
            group_repeat[group.id]["thisMsg"] = message[1].asDisplay()
            # lock.release()
        if len(message) > 1 and message[0] == "None":

            # await app.sendGroupMessage(group, MessageChain(__root__=[
            #     Plain("This message was sent by the new version of SAGIRI-Bot")
            # ]))
            program_end = time.time()
            if await get_setting(group.id, "debug"):
                message[1].plus(MessageChain.create([Plain(text=f"\n\nProgram execution time:\n{str(program_end - program_start)}")]))

            await app.sendGroupMessage(group, message[1])
        elif len(message) > 1 and message[0] == "AtSender":

            program_end = time.time()
            if await get_setting(group.id, "debug"):
                message[1].plus(MessageChain.create([Plain(text=f"\n\nProgram execution time:\n{str(program_end - program_start)}")]))

            await app.sendGroupMessage(group, message[1])
        elif len(message) > 1 and message[0] == "quoteSource":

            program_end = time.time()
            if await get_setting(group.id, "debug"):
                message[1].plus(MessageChain.create([Plain(text=f"\n\nProgram execution time:\n{str(program_end - program_start)}")]))

            await app.sendGroupMessage(group, message[1], quote=received_message[Source][0])
        elif len(message) > 1 and message[0] == "revoke":

            program_end = time.time()
            if await get_setting(group.id, "debug"):
                message[1].plus(MessageChain.create([Plain(text=f"\n\nProgram execution time:\n{str(program_end - program_start)}")]))
            msg = await app.sendGroupMessage(group, message[1])
            await asyncio.sleep(20)
            await app.revokeMessage(msg)
        elif len(message) > 1 and message[0] == "setu*":
            for _ in range(message[1]):
                msg = await get_pic("setu", group.id, message_info.sender.id)
                await app.sendGroupMessage(group, msg[1])
                # lock.acquire()
                group_repeat[group.id]["lastMsg"] = group_repeat[group.id]["thisMsg"]
                group_repeat[group.id]["thisMsg"] = msg[1].asDisplay()
                # lock.release()
        elif len(message) > 1 and message[0] == "real*":
            for _ in range(message[1]):
                msg = await get_pic("real", group.id, message_info.sender.id)
                await app.sendGroupMessage(group, msg[1])
                # lock.acquire()
                group_repeat[group.id]["lastMsg"] = group_repeat[group.id]["thisMsg"]
                group_repeat[group.id]["thisMsg"] = msg[1].asDisplay()
                # lock.release()
        elif len(message) > 1 and message[0] == "bizhi*":
            for _ in range(message[1]):
                msg = await get_pic("bizhi", group.id, message_info.sender.id)
                await app.sendGroupMessage(group, msg[1])
                # lock.acquire()
                group_repeat[group.id]["lastMsg"] = group_repeat[group.id]["thisMsg"]
                group_repeat[group.id]["thisMsg"] = msg[1].asDisplay()
                # lock.release()
    except AccountMuted:
        pass
    except ClientResponseError:
        message += [received_message, message_info, group, 1]
        exception_resender_instance.addTask(message)
        # print("Error!!!!!!")


# 定时任务
@sche.schedule(timers.crontabify("30 22 * * *"))
async def declare_dragon():
    groups = await app.groupList()
    print(groups)
    for i in groups:
        print(i.id)
        if await get_setting(i.id, "setu") or await get_setting(i.id, "real"):
            msg = await get_dragon_king(i.id, app)
            await update_dragon_data(i.id, 0, "all")
            print(msg)
            try:
                await app.sendGroupMessage(i.id, msg)
            except AccountMuted:
                pass


@sche.schedule(timers.crontabify("0 0 * * *"))
async def happy_birthday_check_first():
    sql = "UPDATE birthday set announce=false"
    await execute_sql(sql)
    today = datetime.now().strftime("%m-%d")
    groups = await app.groupList()
    for i in groups:
        sql = f"select memberId from birthday where groupId={i.id} and birthday='{today}'"
        members = await execute_sql(sql)
        print(i, members)
        if members:
            members = members[0]
            msg = [Plain(text=f"今天是{today}\n本群有{len(members)}位群友过生日哦~\n它们分别是：\n")]
            for j in members:
                msg.append(At(target=j))
                msg.append(Plain(text="\n"))
            msg.append(Plain(text="让我们祝他们生日快乐！！！"))
            try:
                await app.sendGroupMessage(i.id, MessageChain.create(msg))
                for j in members:
                    sql = f"update birthday set announce=true where memberId={j}"
            except AccountMuted:
                pass


# 初始化
@bcc.receiver("ApplicationLaunched")
async def bot_init(app: GraiaMiraiApplication):
    global frequency_limit_instance
    global exception_resender_instance
    global loop
    print("Bot init start")
    group_list = await app.groupList()
    for i in group_list:
        group_repeat[i.id] = {"lastMsg": "", "thisMsg": "", "stopMsg": ""}
        frequency_limit_dict[i.id] = 0
    await check_group_data_init(group_list)
    frequency_limit_instance = GlobalFrequencyLimitDict(frequency_limit_dict)
    limiter = threading.Thread(target=frequency_limit, args=(frequency_limit_instance,))
    limiter.start()
    exception_resender_instance = ExceptionReSender(app)
    # await exception_resender_listener(app, exception_resender_instance)
    listener = threading.Thread(target=exception_resender_listener, args=(app, exception_resender_instance, loop))
    listener.start()
    print("Bot init end")


@bcc.receiver("FriendMessage")
async def friend_message_listener(
        app: GraiaMiraiApplication,
        friend: Friend,
        message: MessageChain
):
    await friend_message_process(app, friend, message)


@bcc.receiver("GroupMessage")
async def group_message_listener(
        app: GraiaMiraiApplication,
        group: Group,
        message: MessageChain,
        message_info: GroupMessage
):
    program_start = time.time()

    print("接收到组%s中来自%s的消息:%s" % (group.name, message_info.sender.name, message.asDisplay()))

    # 复读
    # lock.acquire()
    group_repeat[group.id]["lastMsg"] = group_repeat[group.id]["thisMsg"]
    group_repeat[group.id]["thisMsg"] = message.asDisplay()
    # print(group_repeat[group.id])
    if group_repeat[group.id]["lastMsg"] != group_repeat[group.id]["thisMsg"]:
        group_repeat[group.id]["stopMsg"] = ""
    if await get_setting(group.id, "repeat"):
        if group_repeat[group.id]["lastMsg"] == group_repeat[group.id]["thisMsg"]:
            if group_repeat[group.id]["thisMsg"] != group_repeat[group.id]["stopMsg"]:
                group_repeat[group.id]["stopMsg"] = group_repeat[group.id]["thisMsg"]
                try:
                    await app.sendGroupMessage(group, message.asSendable())
                except AccountMuted:
                    pass
    # lock.release()

    if message.asDisplay() == "start old version" and message_info.sender.id == await get_config("HostQQ"):
        await app.sendGroupMessage(group, message.create([Plain(text="即将切换至旧版本...")]))
        await app.sendGroupMessage(group, message.create([Plain(text="切换成功！")]))
        os.system("%s \"%s\"" % (await get_config("environment"), await get_config("oldVersion")))

    if message.asDisplay() == "restart bot" and message_info.sender.id == await get_config("HostQQ"):
        await app.sendGroupMessage(group, message.create([Plain(text="即将重启机器人...")]))
        await app.sendGroupMessage(group, message.create([Plain(text="重启成功！")]))
        os.system("%s \"%s\"" % (await get_config("environment"), await get_config("newVersion")))

    if message.asDisplay() == "bot shutdown" and message_info.sender.id == await get_config("HostQQ"):
        await app.sendGroupMessage(group, message.create([Plain(text="即将退出机器人...")]))
        exit(0)

    if message.asDisplay() == "pc shutdown" and message_info.sender.id == await get_config("HostQQ"):
        await app.sendGroupMessage(group, message.create([Plain(text="即将关机...")]))
        os.system("shutdown -s")

    if message.asDisplay() == "test" and message_info.sender.id == await get_config("HostQQ"):
        msg = await get_xml_setu("fs")
        await app.sendGroupMessage(group, msg[1])
    if message.asDisplay() == "test1" and message_info.sender.id == await get_config("HostQQ"):
        # msg = await get_time()
        # msg = await get_group_announcement("测试")\
        msg = await get_douban_new_books()
        await app.sendGroupMessage(group, msg[1])
    if message.asDisplay() == "test2" and message_info.sender.id == await get_config("HostQQ"):
        welcome_json = """
                {
                    "prompt": "欢迎入群",
                    "sourceUrl": "",
                    "extraApps": [],
                    "appID": "",
                    "sourceName": "",
                    "desc": "",
                    "app": "com.tencent.miniapp",
                    "config": {
                        "forward": true
                    },
                    "ver": "1.0.0.89",
                    "view": "all",
                    "meta": {
                        "all": {
                            "preview": "http:/gchat.qpic.cn/gchatpic_new/12904366/1030673292-3125245045-E7FCC807BECA2938EBE5D57E7E4980FF/0?term=2",
                            "title": "欢迎入群",
                            "buttons": [{
                                "name": "---FROM SAGIRI-BOT---",
                                "action": "http://www.qq.com"
                            }],
                            "jumpUrl": "",
                            "summary": "欢迎进群呐~进群了就不许走了呐~\r\n"
                        }
                    },
                    "actionData": "",
                    "actionData_A": ""
                }"""
        print(("test2"))
        await app.sendGroupMessage(
            group.id, MessageChain.create([
                App(content=welcome_json)
            ])
        )
    if message.asDisplay()[:4] == "sql:" and message_info.sender.id == await get_config("HostQQ"):
        result = await execute_sql(message.asDisplay()[4:])
        print(result)
        if type(result) != bool:
            if len(result) > 30:
                await app.sendGroupMessage(group, MessageChain.create([Plain(text="数据过长！自动中止发送！")]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain(text=str(result))]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(text=str(result))]))

    # task = asyncio.create_task(group_message_sender(message_info, message, group, app))
    # tasks.append(task)
    # await asyncio.wait([task], timeout=5)
    # done, pending = await asyncio.wait(tasks, timeout=120)

    switch = await get_setting(group.id, "switch")
    if switch == "online":
        try:
            message_send = await group_message_process(message, message_info, app, frequency_limit_dict)
        except Exception as e:
            message_send = [
                "quoteSource",
                MessageChain.create([
                    Plain(text=str(e))
                ])
            ]
    elif switch == "offline" and message_info.sender.id != await get_config("HostQQ"):
        message_send = ["None"]
    elif message_info.sender.id == await get_config("HostQQ"):
        try:
            message_send = await group_message_process(message, message_info, app)
        except Exception as e:
            traceback.print_exc()
            message_send = [
                "quoteSource",
                MessageChain.create([
                    Plain(text=str(e))
                ])
            ]
    else:
        message_send = [
            "quoteSource",
            MessageChain.create([
                Plain(text="数据项switch错误！请检查数据库！")
            ])
        ]

    # if len(message_send) >= 2 and message_send[1].has(Image):
    #     message_send.append(group)
    #     tasks.put(message_send)
    # else:
    await group_assist_process(message, message_info, message_send, group, program_start)


@bcc.receiver("MemberJoinEvent")
async def member_join(
        app: GraiaMiraiApplication,
        event: MemberJoinEvent
):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                At(target=event.member.id),
                Plain(text="我是本群小可爱纱雾哟~欢迎呐~一起快活鸭~")
            ])
        )
        # welcome_json = json.dumps(eval(await get_json_code("MemberJoinEvent")))
        # print(welcome_json)
        # welcome_json = """{
        #             "prompt": "[欢迎入群]",
        #             "extraApps": [],
        #             "sourceUrl": "",
        #             "appID": "",
        #             "sourceName": "",
        #             "desc": "",
        #             "app": "com.tencent.qqpay.qqmp.groupmsg",
        #             "ver": "1.0.0.7",
        #             "view": "groupPushView",
        #             "meta": {
        #                 "groupPushData": {
        #                     "fromIcon": "",
        #                     "fromName": "name",
        #                     "time": "",
        #                     "report_url": "http:\\/\\/kf.qq.com\\/faq\\/180522RRRVvE180522NzuuYB.html",
        #                     "cancel_url": "http:\\/\\/www.baidu.com",
        #                     "summaryTxt": "",
        #                     "bannerTxt": "欸嘿~欢迎进群呐~进来了就不许走了哦~",
        #                     "item1Img": "",
        #                     "bannerLink": "",
        #                     "bannerImg": "http:\\/\\/gchat.qpic.cn\\/gchatpic_new\\/12904366\\/1046209507-2584598286-E7FCC807BECA2938EBE5D57E7E4980FF\\/0?term=2"
        #                 }
        #             },
        #             "actionData": "",
        #             "actionData_A": ""
        #         }"""
        welcome_json = """
        {
            "prompt": "SAGIRI",
            "sourceUrl": "",
            "extraApps": [],
            "appID": "",
            "sourceName": "",
            "desc": "",
            "app": "com.tencent.miniapp",
            "config": {
                "forward": true
            },
            "ver": "1.0.0.89",
            "view": "all",
            "meta": {
                "all": {
                    "preview": "http:\/\/gchat.qpic.cn\/gchatpic_new\/12904366\/1030673292-3125245045-E7FCC807BECA2938EBE5D57E7E4980FF\/0?term=2",
                    "title": "欢迎入群",
                    "buttons": [{
                        "name": "---FROM SAGIRI-BOT---",
                        "action": "http:\/\/www.qq.com"
                    }],
                    "jumpUrl": "",
                    "summary": "欢迎进群呐~进群了就不许走了呐~\r\n"
                }
            },
            "actionData": "",
            "actionData_A": ""
        }"""
        test_json = """
            {
                "app": "com.tencent.mannounce",
                "config": {
                    "ctime": 1610424762,
                    "forward": 0,
                    "token": "190bcca54b1eb9c543676aa1c82762ab"
                },
                "desc": "群公告",
                "extra": {
                    "app_type": 1,
                    "appid": 1101236949,
                    "uin": 1900384123
                },
                "meta": {
                    "mannounce": {
                        "cr": 1,
                        "encode": 1,
                        "fid": "93206d3900000000ba21fd5fa58a0500",
                        "gc": "963453075",
                        "sign": "cbbf90a7cbf1dc938ac5bdb8224fc3cb",
                        "text": "dGVzdA==",
                        "title": "576k5YWs5ZGK",
                        "tw": 1,
                        "uin": "1900384123"
                    }
                },
                "prompt": "[群公告]test",
                "ver": "1.0.0.43",
                "view": "main"
            }"""
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                App(content=welcome_json)
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberLeaveEventQuit")
async def member_leave(app: GraiaMiraiApplication, event: MemberLeaveEventQuit):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                Plain(text="%s怎么走了呐~是因为偷袭了69岁的老同志吗嘤嘤嘤" % event.member.name)
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberMuteEvent")
async def member_muted(app: GraiaMiraiApplication, event: MemberMuteEvent):
    if event.operator is not None:
        if event.member.id == await get_config("HostQQ"):
            try:
                await app.unmute(event.member.group.id, event.member.id)
                await app.sendGroupMessage(
                    event.member.group.id, MessageChain.create([
                        Plain(text="保护！保护！")
                    ])
                )
            except PermissionError:
                pass
        else:
            try:
                m, s = divmod(event.durationSeconds, 60)
                h, m = divmod(m, 60)
                await app.sendGroupMessage(
                    event.member.group.id, MessageChain.create([
                        Plain(text="哦~看看是谁被关进小黑屋了？\n"),
                        Plain(text="哦我的上帝啊~是%s！他将在小黑屋里呆%s哦~" % (event.member.name, "%02d:%02d:%02d" % (h, m, s)))
                    ])
                )
            except AccountMuted:
                pass


@bcc.receiver("MemberUnmuteEvent")
async def member_unmuted(app: GraiaMiraiApplication, event: MemberUnmuteEvent):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                Plain(text="啊嘞嘞？%s被放出来了呢~" % event.member.name)
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberLeaveEventKick")
async def member_kicked(app: GraiaMiraiApplication, event: MemberLeaveEventKick):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                Plain(text="%s滚蛋了呐~" % event.member.name)
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberSpecialTitleChangeEvent")
async def member_special_title_change(app: GraiaMiraiApplication, event: MemberSpecialTitleChangeEvent):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                Plain(text="啊嘞嘞？%s的群头衔从%s变成%s了呐~" % (event.member.name, event.origin, event.current))
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberPermissionChangeEvent")
async def member_permission_change(app: GraiaMiraiApplication, event: MemberPermissionChangeEvent):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                Plain(text="啊嘞嘞？%s的权限变成%s了呐~跪舔大佬！" % (event.member.name, event.current))
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("BotJoinGroupEvent")
async def bot_join_group(app: GraiaMiraiApplication, group: Group):
    print(f"add group {group.name}")
    group_repeat[group.id] = {"lastMsg": "", "thisMsg": "", "stopMsg": ""}
    try:
        await app.sendGroupMessage(
            group, MessageChain.create([
                Plain(text="欸嘿嘿~我来啦！宇宙无敌小可爱纱雾酱华丽登场！")
            ])
        )
    except AccountMuted:
        pass
    await bot_join_group_init(group.id, group.name)


@bcc.receiver("BotLeaveEventKick")
async def bot_leave_group(app: GraiaMiraiApplication, event: BotLeaveEventKick):
    print("bot has been kicked!")
    await app.sendFriendMessage(
        await get_config("HostQQ"), MessageChain.create([
            Plain(text=f"呜呜呜主人我被踢出{event.group.name}群了")
        ])
    )


@bcc.receiver("GroupNameChangeEvent")
async def group_name_changed(app: GraiaMiraiApplication, event: GroupNameChangeEvent):
    try:
        await app.sendGroupMessage(
            event.group, MessageChain.create([
                Plain(text=f"群名改变啦！告别过去，迎接未来哟~\n本群名称由{event.origin}变为{event.current}辣！")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupEntranceAnnouncementChangeEvent")
async def group_entrance_announcement_changed(app: GraiaMiraiApplication, event: GroupEntranceAnnouncementChangeEvent):
    try:
        await app.sendGroupMessage(
            event.group, MessageChain.create([
                Plain(text=f"入群公告改变啦！注意查看呐~\n原公告：{event.origin}\n新公告：{event.current}")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupAllowAnonymousChatEvent")
async def group_allow_anonymous_chat_changed(app: GraiaMiraiApplication, event: GroupAllowAnonymousChatEvent):
    try:
        await app.sendGroupMessage(
            event.group, MessageChain.create([
                Plain(text=f"匿名功能现在{'开启辣！畅所欲言吧！' if event.current else '关闭辣！光明正大做人吧！'}")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupAllowConfessTalkEvent")
async def group_allow_confess_talk_changed(app: GraiaMiraiApplication, event: GroupAllowConfessTalkEvent):
    try:
        await app.sendGroupMessage(
            event.group, MessageChain.create([
                Plain(text=f"坦白说功能现在{'开启辣！快来让大家更加了解你吧！' if event.current else '关闭辣！有时候也要给自己留点小秘密哟~'}")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupAllowMemberInviteEvent")
async def group_allow_member_invite_changed(app: GraiaMiraiApplication, event: GroupAllowMemberInviteEvent):
    try:
        await app.sendGroupMessage(
            event.group, MessageChain.create([
                Plain(text=f"现在{'允许邀请成员加入辣！快把朋友拉进来玩叭！' if event.current else '不允许邀请成员加入辣！要注意哦~'}")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberCardChangeEvent")
async def member_card_changed(app: GraiaMiraiApplication, event: MemberCardChangeEvent, group: Group):
    try:
        await app.sendGroupMessage(
            group, MessageChain.create([
                Plain(text=f"啊嘞嘞？{event.member.name}的群名片被{event.operator.name}从{event.origin}改为{event.current}了呢！")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("NewFriendRequestEvent")
async def new_friend_request(app: GraiaMiraiApplication, event: NewFriendRequestEvent):
    await app.sendFriendMessage(
        await get_config("HostQQ"), MessageChain.create([
            Plain(text=f"主人主人，有个人来加我好友啦！\n"),
            Plain(text=f"ID：{event.supplicant}\n"),
            Plain(text=f"来自：{event.nickname}\n"),
            Plain(text=f"描述：{event.message}\n"),
            Plain(text=f"source：{event.sourceGroup}")
        ])
    )


@bcc.receiver("MemberJoinRequestEvent")
async def new_member_join_request(app: GraiaMiraiApplication, event: MemberJoinRequestEvent):
    try:
        await app.sendGroupMessage(
            event.groupId, MessageChain.create([
                Plain(text=f"有个新的加群加群请求哟~管理员们快去看看叭！\n"),
                Plain(text=f"ID：{event.supplicant}\n"),
                Plain(text=f"昵称：{event.nickname}\n"),
                Plain(text=f"描述：{event.message}\n")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("BotInvitedJoinGroupRequestEvent")
async def bot_invited_join_group(app: GraiaMiraiApplication, event: BotInvitedJoinGroupRequestEvent):
    if event.supplicant != await get_config("HostQQ"):
        await app.sendFriendMessage(
            await get_config("HostQQ"), MessageChain.create([
                Plain(text=f"主人主人，有个人拉我进群啦！\n"),
                Plain(text=f"ID：{event.supplicant}\n"),
                Plain(text=f"来自：{event.nickname}\n"),
                Plain(text=f"描述：{event.message}\n")
            ])
        )


# @bcc.receiver("GroupRecallEvent")
# async def anti_revoke(app: GraiaMiraiApplication, event: GroupRecallEvent):
#     print("revoke!")
#     try:
#         await app.sendGroupMessage(
#             event.group,
#             await app.messageFromId(event.messageId).messagechain
#         )
#     except AccountMuted:
#         pass


app.launch_blocking()
