import traceback

from loguru import logger
from dateutil.relativedelta import relativedelta

from graia.ariadne.app import Ariadne
from graia.ariadne.event.mirai import *
from graia.ariadne.message.element import *
from graia.ariadne.event.message import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.exception import AccountMuted, UnknownTarget

from sagiri_bot.utils import get_setting
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.orm.async_orm import orm, UserPermission, Setting
from sagiri_bot.frequency_limit_module import GlobalFrequencyLimitDict

core: AppCore = AppCore.get_core_instance()
bcc = core.get_bcc()
config = core.get_config()


@bcc.receiver("MemberJoinEvent")
async def member_join(app: Ariadne, event: MemberJoinEvent):
    try:
        await app.sendMessage(
            event.member.group, MessageChain.create([
                At(target=event.member.id),
                Plain(text="我是本群小可爱纱雾哟~欢迎呐~一起快活鸭~")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberLeaveEventQuit")
async def member_leave(app: Ariadne, event: MemberLeaveEventQuit):
    try:
        await app.sendMessage(
            event.member.group, MessageChain.create([
                Plain(text="%s怎么走了呐~是因为偷袭了69岁的老同志吗嘤嘤嘤" % event.member.name)
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberMuteEvent")
async def member_muted(app: Ariadne, event: MemberMuteEvent):
    if event.operator is not None:
        if event.member.id == config.host_qq:
            try:
                await app.unmuteMember(event.member.group, event.member)
                await app.sendMessage(
                    event.member.group, MessageChain.create([
                        Plain(text="保护！保护！")
                    ])
                )
            except PermissionError:
                pass
        else:
            try:
                m, s = divmod(event.durationSeconds, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                await app.sendMessage(
                    event.member.group, MessageChain.create([
                        Plain(text="哦~看看是谁被关进小黑屋了？\n"),
                        Plain(
                            text="哦我的上帝啊~是%s！他将在小黑屋里呆%s哦~" %
                                 (event.member.name, "%d天%02d小时%02d分钟%02d秒" % (d, h, m, s))
                        )
                    ])
                )
            except AccountMuted:
                pass


@bcc.receiver("MemberUnmuteEvent")
async def member_unmute(app: Ariadne, event: MemberUnmuteEvent):
    try:
        await app.sendMessage(
            event.member.group, MessageChain.create([
                Plain(text="啊嘞嘞？%s被放出来了呢~" % event.member.name)
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberLeaveEventKick")
async def member_kicked(app: Ariadne, event: MemberLeaveEventKick):
    try:
        await app.sendMessage(
            event.member.group, MessageChain.create([
                Plain(text="%s滚蛋了呐~" % event.member.name)
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberSpecialTitleChangeEvent")
async def member_special_title_change(app: Ariadne, event: MemberSpecialTitleChangeEvent):
    try:
        await app.sendMessage(
            event.member.group, MessageChain.create([
                Plain(text="啊嘞嘞？%s的群头衔从%s变成%s了呐~" % (event.member.name, event.origin, event.current))
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("MemberPermissionChangeEvent")
async def member_permission_change(app: Ariadne, event: MemberPermissionChangeEvent):
    try:
        await app.sendMessage(
            event.member.group, MessageChain.create([
                Plain(text="啊嘞嘞？%s的权限变成%s了呐~跪舔大佬！" % (event.member.name, event.current))
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("BotLeaveEventKick")
async def bot_leave_group(app: Ariadne, event: BotLeaveEventKick):
    print("bot has been kicked!")
    await app.sendFriendMessage(
        config.host_qq, MessageChain.create([
            Plain(text=f"呜呜呜主人我被踢出{event.group.name}群了")
        ])
    )


@bcc.receiver("GroupNameChangeEvent")
async def group_name_changed(app: Ariadne, event: GroupNameChangeEvent):
    try:
        await app.sendMessage(
            event.group, MessageChain.create([
                Plain(text=f"群名改变啦！告别过去，迎接未来哟~\n本群名称由{event.origin}变为{event.current}辣！")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupEntranceAnnouncementChangeEvent")
async def group_entrance_announcement_changed(app: Ariadne, event: GroupEntranceAnnouncementChangeEvent):
    try:
        await app.sendMessage(
            event.group, MessageChain.create([
                Plain(text=f"入群公告改变啦！注意查看呐~\n原公告：{event.origin}\n新公告：{event.current}")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupAllowAnonymousChatEvent")
async def group_allow_anonymous_chat_changed(app: Ariadne, event: GroupAllowAnonymousChatEvent):
    try:
        await app.sendMessage(
            event.group, MessageChain.create([
                Plain(text=f"匿名功能现在{'开启辣！畅所欲言吧！' if event.current else '关闭辣！光明正大做人吧！'}")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupAllowConfessTalkEvent")
async def group_allow_confess_talk_changed(app: Ariadne, event: GroupAllowConfessTalkEvent):
    try:
        await app.sendMessage(
            event.group, MessageChain.create([
                Plain(text=f"坦白说功能现在{'开启辣！快来让大家更加了解你吧！' if event.current else '关闭辣！有时候也要给自己留点小秘密哟~'}")
            ])
        )
    except AccountMuted:
        pass


@bcc.receiver("GroupAllowMemberInviteEvent")
async def group_allow_member_invite_changed(app: Ariadne, event: GroupAllowMemberInviteEvent):
    try:
        await app.sendMessage(
            event.group, MessageChain.create([
                Plain(text=f"现在{'允许邀请成员加入辣！快把朋友拉进来玩叭！' if event.current else '不允许邀请成员加入辣！要注意哦~'}")
            ])
        )
    except AccountMuted:
        pass


# @bcc.receiver("MemberCardChangeEvent")
async def member_card_changed(app: Ariadne, event: MemberCardChangeEvent, group: Group):
    try:
        if event.operator:
            if event.member.name == event.origin or event.origin == "" or event.current == "":
                pass
            else:
                await app.sendMessage(
                    group, MessageChain.create([
                        Plain(
                            f"啊嘞嘞？{event.member.name}的群名片被{event.operator.name}"
                            f"从{event.origin}改为{event.current}了呢！"
                        )
                    ])
                )
        else:
            if event.member.name == event.origin or event.origin == "" or event.current == "":
                pass
            else:
                await app.sendMessage(
                    group, MessageChain.create([
                        Plain(text=f"啊嘞嘞？{event.member.name}的群名片从{event.origin}改为{event.current}了呢！")
                    ])
                )
    except AccountMuted:
        pass


@bcc.receiver("NewFriendRequestEvent")
async def new_friend_request(app: Ariadne, event: NewFriendRequestEvent):
    await app.sendFriendMessage(
        config.host_qq, MessageChain.create([
            Plain(text=f"主人主人，有个人来加我好友啦！\n"),
            Plain(text=f"ID：{event.supplicant}\n"),
            Plain(text=f"来自：{event.nickname}\n"),
            Plain(text=f"描述：{event.message}\n"),
            Plain(text=f"source：{event.sourceGroup}")
        ])
    )


@bcc.receiver("MemberJoinRequestEvent")
async def new_member_join_request(app: Ariadne, event: MemberJoinRequestEvent):
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
async def bot_invited_join_group(app: Ariadne, event: BotInvitedJoinGroupRequestEvent):
    if event.supplicant != config.host_qq:
        await app.sendFriendMessage(
            config.host_qq, MessageChain.create([
                Plain(text=f"主人主人，有个人拉我进群啦！\n"),
                Plain(text=f"ID：{event.supplicant}\n"),
                Plain(text=f"来自：{event.nickname}\n"),
                Plain(text=f"描述：{event.message}\n")
            ])
        )


@bcc.receiver("GroupRecallEvent")
async def anti_revoke(app: Ariadne, event: GroupRecallEvent):
    if await get_setting(event.group.id, Setting.anti_revoke) and event.authorId != config.bot_qq:
        try:
            msg = await app.getMessageFromId(event.messageId)
            revoked_msg = msg.messageChain
            author_member = await app.getMember(event.group.id, event.authorId)
            author_name = "自己" if event.operator.id == event.authorId else author_member.name
            resend_msg = sum(
                MessageChain.create([Plain(text=f"{event.operator.name}偷偷撤回了{author_name}的一条消息哦：\n\n")]),
                revoked_msg
            )
            await app.sendMessage(
                event.group,
                resend_msg.asSendable()
            )
        except (AccountMuted, UnknownTarget):
            pass


@bcc.receiver("BotJoinGroupEvent")
async def bot_join_group(app: Ariadne, group: Group):
    logger.info(f"机器人加入群组 <{group.name}>")
    try:
        await orm.insert_or_update(
            Setting,
            [Setting.group_id == group.id],
            {"group_id": group.id, "group_name": group.name, "active": True}
        )
        await orm.insert_or_update(
            UserPermission,
            [UserPermission.member_id == config.host_qq, UserPermission.group_id == group.id],
            {"member_id": config.host_qq, "group_id": group.id, "level": 4}
        )
        GlobalFrequencyLimitDict().add_group(group.id)
        await app.sendMessage(
            group, MessageChain.create([
                Plain(text="欸嘿嘿~我来啦！宇宙无敌小可爱纱雾酱华丽登场！")
            ])
        )
    except AccountMuted:
        pass
    except:
        logger.error(traceback.format_exc())
nudge_info = {}


@bcc.receiver("NudgeEvent")
async def nudge(app: Ariadne, event: NudgeEvent):
    if event.target == config.bot_qq:
        if event.context_type == "group":
            if member := await app.getMember(event.group_id, event.supplicant):
                logger.info(f"机器人被群 <{member.group.name}> 中用户 <{member.name}> 戳了戳。")
                if member.group.id in nudge_info.keys():
                    if member.id in nudge_info[member.group.id].keys():
                        period = nudge_info[member.group.id][member.id]["time"] + relativedelta(minutes=1)
                        if datetime.now() >= period:
                            nudge_info[member.group.id][member.id] = {"count": 0, "time": datetime.now()}
                        count = nudge_info[member.group.id][member.id]["count"] + 1
                        if count == 1:
                            try:
                                await app.sendNudge(member)
                            except:
                                pass
                            nudge_info[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 2:
                            try:
                                await app.sendNudge(member)
                                await app.sendMessage(
                                    member.group, MessageChain.create([
                                        Plain(text=f"不许戳了！")
                                    ])
                                )
                            except:
                                pass
                            nudge_info[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 3:
                            try:
                                await app.sendNudge(member)
                                await app.sendMessage(
                                    member.group, MessageChain.create([
                                        Plain(text=f"说了不许再戳了！")
                                    ])
                                )
                            except:
                                pass
                            nudge_info[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 4:
                            try:
                                await app.sendNudge(member)
                            except:
                                pass
                            nudge_info[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 5:
                            try:
                                await app.sendNudge(member)
                                await app.sendMessage(
                                    member.group, MessageChain.create([
                                        Plain(text=f"呜呜呜你欺负我，不理你了！")
                                    ])
                                )
                            except:
                                pass
                            nudge_info[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif 6 <= count <= 9:
                            nudge_info[member.group.id][member.id] = {"count": count, "time": datetime.now()}
                        elif count == 10:
                            try:
                                await app.sendNudge(member)
                                await app.sendMessage(
                                    member.group, MessageChain.create([
                                        Plain(text="你真的很有耐心欸。")
                                    ])
                                )
                            except:
                                pass
                    else:
                        nudge_info[member.group.id][member.id] = {"count": 1, "time": datetime.now()}
                        await app.sendNudge(member)
                else:
                    nudge_info[member.group.id] = {member.id: {"count": 1, "time": datetime.now()}}
                    await app.sendNudge(member)
        else:
            if friend := await app.getFriend(event.supplicant):
                logger.info(f"机器人被好友 <{friend.nickname}> 戳了戳。")
