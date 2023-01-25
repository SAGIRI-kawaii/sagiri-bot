# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
from loguru import logger

from creart import create
from graia.saya import Saya
from graia.ariadne import Ariadne
from graia.broadcast import Broadcast
from graia.ariadne.event.lifecycle import AccountLaunch
from graia.ariadne.event.message import ActiveFriendMessage, ActiveGroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member, Friend, Stranger

from core import Sagiri
from shared.funcs import online_notice
from shared.models.config import GlobalConfig
from shared.models.public_group import PublicGroup
from shared.models.frequency_limit import GlobalFrequencyLimitDict

config = create(GlobalConfig)
bcc = create(Broadcast)
saya = create(Saya)


@bcc.receiver("GroupMessage")
async def group_message_handler(app: Ariadne, message: MessageChain, group: Group, member: Member):
    create(Sagiri).received_count += 1
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(
        f"收到来自 Bot <{app.account}> 群 <{group.name.strip()}> 中成员 <{member.name.strip()}> 的消息：{message_text_log}"
    )


@bcc.receiver("FriendMessage")
async def friend_message_listener(app: Ariadne, friend: Friend, message: MessageChain):
    create(Sagiri).received_count += 1
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(f"收到来自 Bot<{app.account}> 好友 <{friend.nickname.strip()}> 的消息：{message_text_log}")


@bcc.receiver("TempMessage")
async def temp_message_listener(app: Ariadne, member: Member, message: MessageChain):
    create(Sagiri).received_count += 1
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(
        f"收到来自 Bot <{app.account}> 群 <{member.group.name.strip()}> 中成员 <{member.name.strip()}> 的临时消息：{message_text_log}"
    )


@bcc.receiver("StrangerMessage")
async def stranger_message_listener(app: Ariadne, stranger: Stranger, message: MessageChain):
    create(Sagiri).received_count += 1
    message_text_log = message.display.replace("\n", "\\n").strip()
    logger.info(f"收到来自 Bot <{app.account}> 陌生人 <{stranger.nickname.strip()}> 的消息：{message_text_log}")


@bcc.receiver("ActiveGroupMessage")
async def active_group_message_handler(app: Ariadne, event: ActiveGroupMessage):
    create(Sagiri).sent_count += 1
    # if event.message_chain[Source][0].id == -1:
    #     return await app.send_group_message(event.subject, MessageChain("发送失败，可能被风控"))
    message_text_log = event.message_chain.display.replace("\n", "\\n").strip()
    logger.info(f"成功向 Bot <{app.account}> 群 <{event.subject.name.strip()}> 发送消息：{message_text_log}")


@bcc.receiver("ActiveFriendMessage")
async def active_friend_message_handler(app: Ariadne, event: ActiveFriendMessage):
    create(Sagiri).sent_count += 1
    message_text_log = event.message_chain.display.replace("\n", "\\n").strip()
    logger.info(f"成功向 Bot <{app.account}> 好友 <{event.subject.nickname.strip()}> 发送消息：{message_text_log}")


@bcc.receiver(AccountLaunch)
async def init(event: AccountLaunch):
    core = create(Sagiri)
    _ = await core.initialize()
    _ = await core.public_group_init(event.app)
    await online_notice(event.app.account)


@bcc.receiver(AccountLaunch)
async def frequency_limit_run():
    await create(GlobalFrequencyLimitDict).frequency_limit()


@bcc.receiver(AccountLaunch)
async def accounts_check_run():
    await create(PublicGroup).accounts_check()


if __name__ == '__main__':
    if Path.cwd() != Path(__file__).parent.absolute():
        logger.critical(f"当前目录非项目所在目录！请进入{str(Path(__file__).parent)}后再运行 SAGIRI-BOT!")
        exit(0)

    parser = argparse.ArgumentParser(description='命令行中传入一个数字')
    parser.add_argument('--set-config', action="store_true", help="配置文件更改", dest="set_config")
    args = parser.parse_args()
    if args.set_config:
        from shared.utils.tui import set_config
        set_config()
    else:
        core = create(Sagiri)
        core.install_modules(Path("modules") / "self_contained")
        core.install_modules(Path("modules") / "third_party")
        core.install_modules(Path("modules") / "required")
        core.launch()
