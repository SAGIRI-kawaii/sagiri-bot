import contextlib
from creart import create
from graia.ariadne import Ariadne
from graia.ariadne.exception import AccountMuted
from graia.ariadne.message.chain import MessageChain

from shared.orm import Setting
from shared.models.group_setting import GroupSetting


async def online_notice(account: int | None = None):
    app = Ariadne.current(account)
    group_list = await app.get_group_list()
    group_setting = create(GroupSetting)
    for group in group_list:
        if await group_setting.get_setting(group.id, Setting.online_notice):
            with contextlib.suppress(AccountMuted):
                await app.send_group_message(group, MessageChain("纱雾酱打卡上班啦！"))
