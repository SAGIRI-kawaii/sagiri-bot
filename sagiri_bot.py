# -*- coding: utf-8 -*-
import asyncio

from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session

from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import App
from graia.application.message.elements.internal import Source
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.exceptions import *

from SAGIRIBOT.process.message_process import group_message_process
from SAGIRIBOT.basics.bot_join_group_init import bot_join_group_init
from SAGIRIBOT.basics.check_group_data_init import check_group_data_init
from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.data_manage.get_data.get_setting import get_setting
from SAGIRIBOT.images.get_image import get_pic

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080",
        authKey="1234567890",
        account=1785007019,
        websocket=True
    )
)

# 复读判断
group_repeat = dict()

async def group_assist_process(received_message: MessageChain, message_info: GroupMessage, message: list, group: Group) -> None:
    """
    Complete the auxiliary work that the function: message_process has not completed

    Args:
        received_message: Received message
        message: message list([what_needs_to_be_done, message_to_be_send])
        group: Group class from the receive message

    Examples:
        await group_assist_process(message, message_send, group)

    Return:
        None
    """
    try:
        if len(message) > 1 and "*" not in message[0]:
            group_repeat[group.id]["lastMsg"] = group_repeat[group.id]["thisMsg"]
            group_repeat[group.id]["thisMsg"] = message[1].asDisplay()
        if len(message) > 1 and message[0] == "None":
            await app.sendGroupMessage(group, MessageChain(__root__=[
                Plain("This message was sent by the new version of SAGIRI-Bot")
            ]))
            await app.sendGroupMessage(group, message[1])
        elif len(message) > 1 and message[0] == "AtSender":
            await app.sendGroupMessage(group, message[1])
        elif len(message) > 1 and message[0] == "quoteSource":
            await app.sendGroupMessage(group, message[1], quote=received_message[Source][0])
        elif len(message) > 1 and message[0] == "revoke":
            msg = await app.sendGroupMessage(group, message[1])
            await asyncio.sleep(20)
            await app.revokeMessage(msg)
        elif len(message) > 1 and message[0] == "setu*":
            for _ in range(message[1]):
                message = await get_pic("setu", group.id, message_info.sender.id)
                await app.sendGroupMessage(group, message[1])
        elif len(message) > 1 and message[0] == "real*":
            for _ in range(message[1]):
                message = await get_pic("real", group.id, message_info.sender.id)
                await app.sendGroupMessage(group, message[1])
        elif len(message) > 1 and message[0] == "bizhi*":
            for _ in range(message[1]):
                message = await get_pic("bizhi", group.id, message_info.sender.id)
                await app.sendGroupMessage(group, message[1])
    except AccountMuted:
        pass


@bcc.receiver("ApplicationLaunched")
async def bot_init(app: GraiaMiraiApplication):
    print("Bot init start")
    group_list = await app.groupList()
    for i in group_list:
        group_repeat[i.id] = {"lastMsg": "", "thisMsg": "", "stopMsg": ""}
    await check_group_data_init(group_list)
    # for i in group_list:
    #     await app.sendGroupMessage(i, MessageChain.create([
    #         Plain(text="SAGIRI-Bot is online")
    #     ]))
    print("Bot init end")


@bcc.receiver("FriendMessage")
async def friend_message_listener(
        app: GraiaMiraiApplication,
        friend: Friend,
        message: MessageChain
):
    await app.sendFriendMessage(friend, MessageChain(__root__=[
        Plain("你好！")
    ]))


@bcc.receiver("GroupMessage")
async def group_message_listener(
        app: GraiaMiraiApplication,
        group: Group,
        message: MessageChain,
        message_info: GroupMessage
):
    print("接收到组%s中来自%s的消息:%s" % (group.name, message_info.sender.name, message.asDisplay()))

    # 复读
    group_repeat[group.id]["lastMsg"] = group_repeat[group.id]["thisMsg"]
    group_repeat[group.id]["thisMsg"] = message.asDisplay()
    # print(group_repeat[group.id])
    if group_repeat[group.id]["lastMsg"] != group_repeat[group.id]["thisMsg"]:
        group_repeat[group.id]["stopMsg"] = ""
    if await get_setting(group.id, "repeat"):
        if group_repeat[group.id]["lastMsg"] == group_repeat[group.id]["thisMsg"]:
            if group_repeat[group.id]["thisMsg"] != group_repeat[group.id]["stopMsg"]:
                group_repeat[group.id]["stopMsg"] = group_repeat[group.id]["thisMsg"]
                await app.sendGroupMessage(group, message.asSendable())

    message_send = await group_message_process(message, message_info)
    print(message)
    await group_assist_process(message, message_info, message_send, group)


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
        welcome_json = """{
                    "prompt": "[欢迎入群]",
                    "extraApps": [],
                    "sourceUrl": "",
                    "appID": "",
                    "sourceName": "",
                    "desc": "",
                    "app": "com.tencent.qqpay.qqmp.groupmsg",
                    "ver": "1.0.0.7",
                    "view": "groupPushView",
                    "meta": {
                        "groupPushData": {
                            "fromIcon": "",
                            "fromName": "name",
                            "time": "",
                            "report_url": "http:\\/\\/kf.qq.com\\/faq\\/180522RRRVvE180522NzuuYB.html",
                            "cancel_url": "http:\\/\\/www.baidu.com",
                            "summaryTxt": "",
                            "bannerTxt": "欸嘿~欢迎进群呐~进来了就不许走了哦~",
                            "item1Img": "",
                            "bannerLink": "",
                            "bannerImg": "http:\\/\\/gchat.qpic.cn\\/gchatpic_new\\/12904366\\/1046209507-2584598286-E7FCC807BECA2938EBE5D57E7E4980FF\\/0?term=2"
                        }
                    },
                    "actionData": "",
                    "actionData_A": ""
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
                Plain(text="%s怎么走了呐~是纱雾不够可爱吗嘤嘤嘤" % event.member.name)
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
                await app.sendGroupMessage(
                    event.member.group.id, MessageChain.create([
                        Plain(text="哦~看看是谁被关进小黑屋了？\n"),
                        Plain(text="哦我的上帝啊~是%s！他将在小黑屋里呆%s哦~" % (event.member.name, str(event.durationSeconds)))
                    ])
                )
            except AccountMuted:
                pass


@bcc.receiver("MemberUnmuteEvent")
async def member_join(app: GraiaMiraiApplication, event: MemberUnmuteEvent):
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
async def member_join(app: GraiaMiraiApplication, event: MemberSpecialTitleChangeEvent):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                Plain(text="啊嘞嘞？%s的群头衔变成%s了呐~" % (event.member.name, event.current))
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberPermissionChangeEvent")
async def member_join(app: GraiaMiraiApplication, event: MemberPermissionChangeEvent):
    try:
        await app.sendGroupMessage(
            event.member.group.id, MessageChain.create([
                Plain(text="啊嘞嘞？%s的权限变成%s了呐~" % (event.member.name, event.current))
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("BotJoinGroupEvent")
async def member_join(app: GraiaMiraiApplication, event: BotJoinGroupEvent):
    print("add group")
    try:
        await app.sendGroupMessage(
            event.group, MessageChain.create([
                Plain(text="欸嘿嘿~我来啦！宇宙无敌小可爱纱雾酱华丽登场！")
            ])
        )
    except AccountMuted:
        pass
    await bot_join_group_init(event.group.id, event.group.name)


app.launch_blocking()
