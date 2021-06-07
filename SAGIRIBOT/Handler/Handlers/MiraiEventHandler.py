from graia.application.event.mirai import *
from graia.application.event.messages import Group
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.application.exceptions import AccountMuted, UnknownTarget

from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.ORM.AsyncORM import Setting
from SAGIRIBOT.utils import get_config, get_setting

core: AppCore = AppCore.get_core_instance()
bcc = core.get_bcc()
app = core.get_app()


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
        if event.member.id == get_config("HostQQ"):
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


@bcc.receiver("BotLeaveEventKick")
async def bot_leave_group(app: GraiaMiraiApplication, event: BotLeaveEventKick):
    print("bot has been kicked!")
    await app.sendFriendMessage(
        get_config("HostQQ"), MessageChain.create([
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
        get_config("HostQQ"), MessageChain.create([
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
    if event.supplicant != get_config("HostQQ"):
        await app.sendFriendMessage(
            get_config("HostQQ"), MessageChain.create([
                Plain(text=f"主人主人，有个人拉我进群啦！\n"),
                Plain(text=f"ID：{event.supplicant}\n"),
                Plain(text=f"来自：{event.nickname}\n"),
                Plain(text=f"描述：{event.message}\n")
            ])
        )


@bcc.receiver("GroupRecallEvent")
async def anti_revoke(app: GraiaMiraiApplication, event: GroupRecallEvent):
    if await get_setting(event.group.id, Setting.anti_revoke) and event.authorId != get_config("BotQQ"):
        try:
            msg = await app.messageFromId(event.messageId)
            revoked_msg = msg.messageChain
            print(event.authorId)
            author_member = await app.getMember(event.group.id, event.authorId)
            author_name = "自己" if event.operator.id == event.authorId else author_member.name
            resended_msg = MessageChain.join(
                MessageChain.create([Plain(text=f"{event.operator.name}偷偷撤回了{author_name}的一条消息哦：\n\n")]),
                revoked_msg
            )
            print(msg)
            await app.sendGroupMessage(
                event.group,
                resended_msg.asSendable()
            )
        except (AccountMuted, UnknownTarget):
            pass
