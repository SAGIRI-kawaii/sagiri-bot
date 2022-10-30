import json
import contextlib
from pathlib import Path
from loguru import logger

from creart import create
from graia.saya import Channel
from graia.ariadne import Ariadne
from graia.broadcast import Broadcast
from graia.ariadne.event.mirai import *
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.exception import AccountMuted, UnknownTarget
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .utils import *
from shared.orm import orm, UserPermission
from shared.models.config import GlobalConfig
from shared.models.public_group import PublicGroup
from shared.utils.waiter import FriendConfirmWaiter
from shared.models.group_setting import GroupSetting
from shared.utils.control import Function, Distribute
from shared.models.frequency_limit import GlobalFrequencyLimitDict

channel = Channel.current()

channel.name("MiraiEvent")
channel.author("SAGIRI-kawaii")
channel.description("对各种事件响应")

config = create(GlobalConfig)
group_setting = create(GroupSetting)
with open(str(Path(__file__).parent / "events_config.json"), "r", encoding="utf-8") as f:
    event_config = json.load(f)


@channel.use(
    ListenerSchema(
        listening_events=[MemberLeaveEventQuit],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_leave_event_quit(app: Ariadne, group: Group, member: Member):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(event_config["MemberLeaveEventQuit"].format(**unpack_member(member), **unpack_group(group)))
        )


@channel.use(
    ListenerSchema(
        listening_events=[MemberMuteEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_mute_event(app: Ariadne, group: Group, member: Member, event: MemberMuteEvent):
    if event.operator is not None:
        if member.id == config.host_qq:
            with contextlib.suppress(PermissionError):
                await app.unmute_member(group, member)
                await app.send_message(group, MessageChain("保护！保护！"))
        else:
            with contextlib.suppress(AccountMuted):
                m, s = divmod(event.duration, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                await app.send_message(
                    event.member.group,
                    MessageChain(
                        event_config["MemberMuteEvent"].format(
                            duration=event.duration,
                            day="%d" % d,
                            hour="%02d" % h,
                            minute="%02d" % m,
                            second="%02d" % s,
                            **unpack_member(member),
                            **unpack_group(group)
                        )
                    ),
                )


@channel.use(
    ListenerSchema(
        listening_events=[MemberUnmuteEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_unmute_event(app: Ariadne, group: Group, member: Member, event: MemberUnmuteEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            event.member.group,
            MessageChain(
                event_config["MemberUnmuteEvent"].format(
                    **unpack_operator(event.operator),
                    **unpack_member(member),
                    **unpack_group(group)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[MemberLeaveEventKick],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_leave_event_kick(app: Ariadne, group: Group, member: Member, event: MemberLeaveEventKick):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            event.member.group,
            MessageChain(
                event_config["MemberLeaveEventKick"].format(
                    **unpack_operator(event.operator),
                    **unpack_member(member),
                    **unpack_group(group)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[MemberLeaveEventKick],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_leave_event_kick(
    app: Ariadne, group: Group, member: Member, event: MemberLeaveEventKick
):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            event.member.group,
            MessageChain(
                event_config["MemberLeaveEventKick"].format(
                    **unpack_operator(event.operator),
                    **unpack_member(member),
                    **unpack_group(group)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[MemberSpecialTitleChangeEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_special_title_change_event(
    app: Ariadne, group: Group, member: Member, event: MemberSpecialTitleChangeEvent
):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            event.member.group,
            MessageChain(
                event_config["MemberSpecialTitleChangeEvent"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_member(member),
                    **unpack_group(group)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[MemberPermissionChangeEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_permission_change_event(
    app: Ariadne, group: Group, member: Member, event: MemberPermissionChangeEvent
):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            event.member.group,
            MessageChain(
                event_config["MemberPermissionChangeEvent"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_member(member),
                    **unpack_group(group)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[BotLeaveEventKick],
        decorators=[Function.require(channel.module)]
    )
)
async def bot_leave_event_kick(app: Ariadne, group: Group, member: Member):
    create(PublicGroup).remove_group(group, app.account)
    with contextlib.suppress(UnknownTarget):
        await app.send_friend_message(
            config.host_qq,
            MessageChain(
                event_config["BotLeaveEventKick"].format(
                    **unpack_operator(member),
                    **unpack_group(group)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupNameChangeEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def group_name_change_event(app: Ariadne, group: Group, event: GroupNameChangeEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(
                event_config["GroupNameChangeEvent"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupEntranceAnnouncementChangeEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def group_entrance_announcement_change_event(
    app: Ariadne, group: Group, event: GroupEntranceAnnouncementChangeEvent
):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(
                event_config["GroupEntranceAnnouncementChangeEvent"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupAllowAnonymousChatEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def group_allow_anonymous_chat_event(app: Ariadne, group: Group, event: GroupAllowAnonymousChatEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(
                event_config["GroupEntranceAnnouncementChangeEvent"]["open"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
                if event.current else
                event_config["GroupEntranceAnnouncementChangeEvent"]["close"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupAllowConfessTalkEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def group_allow_confess_talk_event(app: Ariadne, group: Group, event: GroupAllowConfessTalkEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(
                event_config["GroupAllowConfessTalkEvent"]["open"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
                if event.current else
                event_config["GroupAllowConfessTalkEvent"]["close"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupAllowMemberInviteEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def group_allow_member_invite_event(app: Ariadne, group: Group, event: GroupAllowMemberInviteEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(
                event_config["GroupAllowMemberInviteEvent"]["open"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
                if event.current else
                event_config["GroupAllowMemberInviteEvent"]["close"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_operator(event.operator)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[MemberCardChangeEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_card_change_event(app: Ariadne, group: Group, member: Member, event: MemberCardChangeEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(
                event_config["MemberCardChangeEvent"].format(
                    origin=event.origin,
                    current=event.current,
                    **unpack_group(group),
                    **unpack_member(member),
                    **unpack_operator(event.operator)
                )
            ),
        )


@channel.use(ListenerSchema(listening_events=[NewFriendRequestEvent]))
async def new_friend_request_event(app: Ariadne, event: NewFriendRequestEvent):
    with contextlib.suppress(AccountMuted, UnknownTarget):
        await app.send_friend_message(
            config.host_qq,
            MessageChain(
                event_config["NewFriendRequestEvent"].format(
                    request_id=event.requestId,
                    supplicant=event.supplicant,
                    nickname=event.nickname,
                    message=event.message,
                    source_group=event.source_group
                )
            ),
        )
        await app.send_friend_message(config.host_qq, MessageChain("若想通过好友申请请在5分钟内回复'通过'"))
        if await InterruptControl(create(Broadcast)).wait(FriendConfirmWaiter(config.host_qq, ["通过"])):
            await event.accept()
            await app.send_friend_message(config.host_qq, MessageChain("好友申请已通过"))


@channel.use(
    ListenerSchema(
        listening_events=[MemberJoinRequestEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_join_request_event(app: Ariadne, event: MemberJoinRequestEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_group_message(
            event.source_group,
            MessageChain(
                event_config["MemberJoinRequestEvent"].format(
                    supplicant=event.supplicant,
                    nickname=event.nickname,
                    message=event.message,
                    source_group=event.source_group,
                    group_name=event.group_name
                )
            ),
        )


@channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
async def bot_invited_join_group_request_event(app: Ariadne, event: BotInvitedJoinGroupRequestEvent):
    with contextlib.suppress(AccountMuted, UnknownTarget):
        await app.send_friend_message(
            config.host_qq,
            MessageChain(
                event_config["BotInvitedJoinGroupRequestEvent"].format(
                    request_id=event.request_id,
                    supplicant=event.supplicant,
                    nickname=event.nickname,
                    message=event.message,
                    source_group=event.source_group,
                    group_name=event.group_name
                )
            ),
        )
        await app.send_friend_message(config.host_qq, MessageChain("若想通过群组邀请请在5分钟内回复'通过'"))
        if await InterruptControl(create(Broadcast)).wait(FriendConfirmWaiter(config.host_qq, ["通过"])):
            _ = await event.accept()
            await app.send_friend_message(config.host_qq, MessageChain("群组邀请已通过"))


@channel.use(
    ListenerSchema(
        listening_events=[BotJoinGroupEvent],
        decorators=[Function.require(channel.module)]
    )
)
async def bot_join_group_event(app: Ariadne, group: Group, event: BotJoinGroupEvent):
    logger.info(f"机器人加入群组 <{group.name}>")
    _ = await create(GroupSetting).add_group(group)
    _ = await orm.insert_or_update(
        UserPermission,
        [
            UserPermission.member_id == config.host_qq,
            UserPermission.group_id == group.id,
        ],
        {"member_id": config.host_qq, "group_id": group.id, "level": 4},
    )
    create(PublicGroup).add_group(group, app.account)
    create(GlobalFrequencyLimitDict).add_group(group.id)
    with contextlib.suppress(AccountMuted, UnknownTarget):
        await app.send_message(
            group,
            MessageChain(
                event_config["BotJoinGroupEvent"].format(
                    **unpack_group(group),
                    **unpack_invitor(event.inviter)
                )
            ),
        )


@channel.use(
    ListenerSchema(
        listening_events=[MemberHonorChangeEvent],
        decorators=[Function.require(channel.module), Distribute.distribute()]
    )
)
async def member_honor_change_event(app: Ariadne, group: Group, member: Member, event: MemberHonorChangeEvent):
    with contextlib.suppress(AccountMuted):
        await app.send_message(
            group,
            MessageChain(
                event_config["MemberHonorChangeEvent"][event.action].format(
                    honor=event.honor,
                    **unpack_group(group),
                    **unpack_member(member),
                )
            ),
        )
