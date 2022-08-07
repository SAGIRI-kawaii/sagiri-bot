import os
import yaml
from pathlib import Path
from loguru import logger

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.event.mirai import *
from graia.ariadne.event.message import Group
from graia.ariadne.message.element import Plain, At
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.exception import AccountMuted, UnknownTarget

from sagiri_bot.config import GlobalConfig
from sagiri_bot.internal_utils import group_setting
from sagiri_bot.orm.async_orm import orm, UserPermission, Setting
from sagiri_bot.frequency_limit_module import GlobalFrequencyLimitDict

config = create(GlobalConfig)

with open(str(Path(os.path.dirname(__file__)) / "event_config.yaml"), "r", encoding='utf-8') as f:
    event_config = yaml.safe_load(f.read())


async def member_join_event(app: Ariadne, group: Group, event: MemberJoinEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.member.group, MessageChain([
                At(target=event.member.id),
                Plain(
                    event_config["member_join_event"].get(
                        str(group.id),
                        event_config["member_join_event"].get("default")
                    ).replace("\\n", "\n").format(group_name=group.name)
                )
            ])
        )
    except AccountMuted:
        pass


# async def member_leave_event_quit(app: Ariadne, group: Group, event: MemberLeaveEventQuit):
#     try:
#         if not await group_setting.get_setting(group, Setting.switch):
#             return None
#         await app.send_message(
#             event.member.group, MessageChain([
#                 Plain(text=f"{event.member.name}怎么走了呐~是因为偷袭了69岁的老同志吗嘤嘤嘤")
#             ])
#         )
#     except AccountMuted:
#         pass


async def member_mute_event(app: Ariadne, group: Group, event: MemberMuteEvent):
    if not await group_setting.get_setting(group, Setting.switch):
        return None
    if event.operator is not None:
        if event.member.id == config.host_qq:
            try:
                await app.unmute_member(event.member.group, event.member)
                await app.send_message(event.member.group, MessageChain("保护！保护！"))
            except PermissionError:
                pass
        else:
            try:
                m, s = divmod(event.duration, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                await app.send_message(
                    event.member.group, MessageChain(
                        "哦~看看是谁被关进小黑屋了？\n"
                        f"哦我的上帝啊~是{event.member.name}！他将在小黑屋里呆{'%d天%02d小时%02d分钟%02d秒' % (d, h, m, s)}哦~"
                    )
                )
            except AccountMuted:
                pass


async def member_unmute_event(app: Ariadne, group: Group, event: MemberUnmuteEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(event.member.group, MessageChain(f"啊嘞嘞？{event.member.name}被放出来了呢~"))
    except AccountMuted:
        pass


async def member_leave_event_kick(app: Ariadne, group: Group, event: MemberLeaveEventKick):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.member.group, MessageChain(f"<{event.member.name}> 被 <{event.operator.name}> 🐏辣~")
        )
    except AccountMuted:
        pass


async def member_special_title_change_event(app: Ariadne, group: Group, event: MemberSpecialTitleChangeEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.member.group,
            MessageChain(f"啊嘞嘞？{event.member.name}的群头衔从{event.origin}变成{event.current}了呐~")
        )
    except AccountMuted:
        pass


async def member_permission_change_event(app: Ariadne, group: Group, event: MemberPermissionChangeEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.member.group, MessageChain(f"啊嘞嘞？{event.member.name}的权限变成{event.current}了呐~")
        )
    except AccountMuted:
        pass


async def bot_leave_event_kick(app: Ariadne, event: BotLeaveEventKick):
    logger.warning("bot has been kicked!")
    await app.send_friend_message(config.host_qq, MessageChain(f"呜呜呜主人我被踢出{event.group.name}群了"))


async def group_name_change_event(app: Ariadne, group: Group, event: GroupNameChangeEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.group,
            MessageChain(f"群名改变啦！告别过去，迎接未来哟~\n本群名称由{event.origin}变为{event.current}辣！")
        )
    except AccountMuted:
        pass


async def group_entrance_announcement_change_event(
        app: Ariadne,
        group: Group,
        event: GroupEntranceAnnouncementChangeEvent
):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.group,
            MessageChain(f"入群公告改变啦！注意查看呐~\n原公告：{event.origin}\n新公告：{event.current}")
        )
    except AccountMuted:
        pass


async def group_allow_anonymous_chat_event(app: Ariadne, group: Group, event: GroupAllowAnonymousChatEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.group,
            MessageChain(f"匿名功能现在{'开启辣！畅所欲言吧！' if event.current else '关闭辣！光明正大做人吧！'}")
        )
    except AccountMuted:
        pass


async def group_allow_confess_talk_event(app: Ariadne, group: Group, event: GroupAllowConfessTalkEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.group,
            MessageChain(
                f"坦白说功能现在{'开启辣！快来让大家更加了解你吧！' if event.current else '关闭辣！有时候也要给自己留点小秘密哟~'}"
            )
        )
    except AccountMuted:
        pass


async def group_allow_member_invite_event(app: Ariadne, group: Group, event: GroupAllowMemberInviteEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        await app.send_message(
            event.group,
            MessageChain(f"现在{'允许邀请成员加入辣！快把朋友拉进来玩叭！' if event.current else '不允许邀请成员加入辣！要注意哦~'}")
        )
    except AccountMuted:
        pass


async def member_card_change_event(app: Ariadne, group: Group, event: MemberCardChangeEvent):
    try:
        if not await group_setting.get_setting(group, Setting.switch):
            return None
        if (
            event.member.name != event.origin
            and event.origin != ""
            and event.current != ""
        ):
            if event.operator:
                await app.send_message(
                    group, MessageChain(
                        f"啊嘞嘞？{event.origin}的群名片被{event.operator.name}"
                        f"改为{event.current}了呢！"
                    )
                )
            else:
                await app.send_message(
                    group,
                    MessageChain(f"啊嘞嘞？{event.origin}的群名片改为{event.current}了呢！")
                )
    except AccountMuted:
        pass


async def new_friend_request_event(app: Ariadne, event: NewFriendRequestEvent):
    await app.send_friend_message(
        config.host_qq, MessageChain([
            Plain(text="主人主人，有个人来加我好友啦！\n"),
            Plain(text=f"ID：{event.supplicant}\n"),
            Plain(text=f"来自：{event.nickname}\n"),
            Plain(text=f"描述：{event.message}\n"),
            Plain(text=f"source：{event.source_group}")
        ])
    )


async def member_join_request_event(app: Ariadne, event: MemberJoinRequestEvent):
    try:
        if not await group_setting.get_setting(event.source_group, Setting.switch):
            return None
        await app.send_group_message(
            event.source_group, MessageChain([
                Plain(text="有个新的加群加群请求哟~管理员们快去看看叭！\n"),
                Plain(text=f"ID：{event.supplicant}\n"),
                Plain(text=f"昵称：{event.nickname}\n"),
                Plain(text=f"描述：{event.message}\n")
            ])
        )
    except AccountMuted:
        pass


async def bot_invited_join_group_request_event(app: Ariadne, event: BotInvitedJoinGroupRequestEvent):
    if event.supplicant != config.host_qq:
        await app.send_friend_message(
            config.host_qq, MessageChain([
                Plain(text="主人主人，有个人拉我进群啦！\n"),
                Plain(text=f"ID：{event.supplicant}\n"),
                Plain(text=f"来自：{event.nickname}\n"),
                Plain(text=f"描述：{event.message}\n")
            ])
        )


async def group_recall_event(app: Ariadne, group: Group, event: GroupRecallEvent):
    if not await group_setting.get_setting(group, Setting.switch):
        return None
    if await group_setting.get_setting(event.group.id, Setting.anti_revoke) and event.author_id != config.bot_qq:
        try:
            msg = await app.get_message_from_id(event.message_id)
            revoked_msg = msg.message_chain.as_sendable()
            author_member = await app.get_member(event.group.id, event.author_id)
            author_name = "自己" if event.operator.id == event.author_id else author_member.name
            resend_msg = MessageChain(f"{event.operator.name}偷偷撤回了{author_name}的一条消息哦：\n\n").extend(revoked_msg)

            await app.send_message(
                event.group,
                resend_msg.as_sendable()
            )
        except (AccountMuted, UnknownTarget):
            pass


async def bot_join_group_event(app: Ariadne, group: Group):
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
        await app.send_message(
            group, MessageChain([
                Plain(text="欸嘿嘿~我来啦！宇宙无敌小可爱纱雾酱华丽登场！")
            ])
        )
    except AccountMuted:
        pass


async def member_honor_change_event(app: Ariadne, group: Group, event: MemberHonorChangeEvent):
    await app.send_message(
        group, MessageChain([
            Plain(text="恭喜" if event.action == 'achieve' else "很遗憾，"),
            At(event.member.id),
            Plain(f"{'获得了' if event.action == 'achieve' else '失去了'} 群荣誉 {event.honor}！"),
        ])
    )
