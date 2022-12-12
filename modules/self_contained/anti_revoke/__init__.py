import contextlib

from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import GroupRecallEvent
from graia.ariadne.message.element import Voice, FlashImage
from graia.ariadne.exception import AccountMuted, UnknownTarget
from graia.saya.builtins.broadcast.schema import ListenerSchema

from shared.orm.tables import Setting
from shared.models.config import GlobalConfig
from shared.models.group_setting import GroupSetting
from shared.utils.control import Function, Distribute

channel = Channel.current()
channel.name("AntiRevoke")
channel.author("SAGIRI-kawaii")
channel.description("一个防撤回的插件，打开开关后自动触发")

config = create(GlobalConfig)
group_setting = create(GroupSetting)


@channel.use(
    ListenerSchema(
        listening_events=[GroupRecallEvent],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module, notice=True),
        ],
    )
)
async def anti_revoke(app: Ariadne, group: Group, event: GroupRecallEvent):
    if not await group_setting.get_setting(group, Setting.switch):
        return None
    if (
        await group_setting.get_setting(event.group.id, Setting.anti_revoke)
        and event.author_id not in config.bot_accounts
    ):
        with contextlib.suppress(AccountMuted, UnknownTarget):
            msg = await app.get_message_from_id(event.message_id, group)
            revoked_msg = msg.message_chain.as_sendable()
            author_member = await app.get_member(event.group.id, event.author_id)
            author_name = "自己" if event.operator.id == event.author_id else author_member.name
            if revoked_msg.has(Voice) or revoked_msg.has(FlashImage):
                await app.send_message(event.group, MessageChain(f"{event.operator.name}偷偷撤回了{author_name}的一条消息哦"))
                await app.send_message(event.group, revoked_msg)
            else:
                resend_msg = MessageChain(f"{event.operator.name}偷偷撤回了{author_name}的一条消息哦：\n\n").extend(revoked_msg)
                await app.send_message(event.group, resend_msg.as_sendable())
