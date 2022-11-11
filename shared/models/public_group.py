import time
import asyncio
from abc import ABC
from typing import Type

from creart import create
from creart import add_creator
from creart import exists_module
from graia.ariadne import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.element import Source
from graia.ariadne.model.relationship import MemberPerm
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.models.config import GlobalConfig


class PublicGroup(object):
    """ group: {accounts} """
    data: dict[int, dict[int, MemberPerm]]
    inited_account: set[int]

    def __init__(self):
        self.data = {}
        self.inited_account = set()
        self.check_running = False

    async def data_init(self):
        config = create(GlobalConfig)
        for account in config.bot_accounts:
            app = Ariadne.current(account)
            for group in await app.get_group_list():
                if group.id in self.data:
                    self.data[group.id][app.account] = group.account_perm
                else:
                    self.data[group.id] = {app.account: group.account_perm}
        print(self.data)

    def add_group(self, group: Group, account: int):
        if group.id in self.data:
            self.data[group.id][account] = group.account_perm
        else:
            self.data[group.id] = {account: group.account_perm}

    def remove_group(self, group: Group | int, account: int):
        group = group.id if isinstance(group, Group) else group
        if group in self.data and self.data[group]:
            del self.data[group][account]

    def get_index(self, group: Group | int, account: int) -> int:
        group = group.id if isinstance(group, Group) else group
        if group in self.data and account in self.data[group]:
            return list(self.data[group]).index(account)
        raise ValueError

    async def add_account(self, *, app: Ariadne | None = None, account: int = None):
        if sum([bool(app), bool(account)]) > 1:
            raise ValueError("Too many binary initializers!")
        if not app and not account:
            raise ValueError("You should give app or account")
        if not app:
            app = Ariadne.current(account)
        for group in await app.get_group_list():
            self.add_group(group, app.account)
        self.inited_account.add(app.account)

    def remove_account(self, account: int):
        self.inited_account.remove(account)
        for group in self.data:
            if account in self.data[group]:
                del self.data[group][account]

    def need_distribute(self, group: Group | int, account: int) -> bool:
        group = group.id if isinstance(group, Group) else group
        if group in self.data and account in self.data[group]:
            return len(self.data[group]) > 1
        return False

    def execution_stop(
        self, group: Group | int, account: int, source: Source | None, require_admin: bool = False
    ) -> bool:
        group_id = group.id if isinstance(group, Group) else group
        if group_id not in self.data:
            self.add_group(group, account)
            return True
        if require_admin:
            if admins := self.get_admin_bots(group):
                if account not in admins:
                    return True
                else:
                    admins.sort()
                    return (source.id + int(time.mktime(source.time.timetuple()))) % len(admins) != admins.index(account)
        if source:
            return (source.id + int(time.mktime(source.time.timetuple()))) % len(self.data[group_id]) != self.get_index(group, account)
        else:
            return int(time.time()) % len(self.data[group_id]) != self.get_index(group, account)

    def get_admin_bots(self, group: Group | int) -> list[int]:
        group = group.id if isinstance(group, Group) else group
        return [i for i in self.data[group] if self.data[group][i] in {MemberPerm.Owner, MemberPerm.Administrator}]

    def account_initialized(self, account: int):
        return account in self.inited_account

    async def accounts_check(self):
        if self.check_running:
            return
        self.check_running = True
        config = create(GlobalConfig)
        while True:
            for account in (await Ariadne.current().get_bot_list()):
                if account in config.bot_accounts and account not in self.inited_account:
                    await self.add_account(account=account)
            for account in self.inited_account:
                if not Ariadne.current(account).connection.status.available:
                    self.remove_account(account)
            await asyncio.sleep(10)


class PublicGroupClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.models.public_group", "PublicGroup"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.models.public_group")

    @staticmethod
    def create(create_type: Type[PublicGroup]) -> PublicGroup:
        return PublicGroup()


add_creator(PublicGroupClassCreator)
