from abc import ABC
from sqlalchemy import select
from typing import Dict, Type, Any
from sqlalchemy.orm.attributes import InstrumentedAttribute

from creart import add_creator
from creart import exists_module
from graia.ariadne.model import Group
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.orm import Setting, orm


class GroupSetting(object):
    data: Dict[int, Dict[str, bool | str]]

    def __init__(self):
        self.data = {}

    async def data_init(self):
        columns = {
            i: Setting.__dict__[i]
            for i in Setting.__dict__.keys()
            if isinstance(Setting.__dict__[i], InstrumentedAttribute)
        }
        column_names = sorted(columns.keys())
        datas = await orm.fetchall(
            select(Setting.group_id, *([columns[name] for name in column_names]))
        )
        for data in datas:
            self.data[data[0]] = dict(zip(column_names, data[1:]))

    async def get_setting(self, group: Group | int, setting: Any) -> bool | str:
        setting_name = str(setting).split(".")[1]
        if isinstance(group, Group):
            group = group.id
        if self.data.get(group, None):
            if res := self.data[group].get(setting_name):
                return res
        else:
            self.data[group] = {}
        if not (result := await orm.fetchone(select(setting).where(Setting.group_id == group))):
            raise ValueError(f"未找到 {group} -> {str(setting)} 结果！请检查数据库！")
        self.data[group][setting_name] = result[0]
        return result[0]

    async def modify_setting(
        self,
        group: Group | int,
        setting: InstrumentedAttribute | str,
        new_value: bool | str,
    ):
        setting_name = (
            str(setting).split(".")[1]
            if isinstance(setting, InstrumentedAttribute)
            else setting
        )
        print("modify:", setting_name)
        if isinstance(group, Group):
            group = group.id
        if self.data.get(group, None):
            self.data[group][setting_name] = new_value
        else:
            self.data[group] = {setting_name: new_value}


class GroupSettingClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.models.group_setting", "GroupSetting"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.models.group_setting")

    @staticmethod
    def create(create_type: Type[GroupSetting]) -> GroupSetting:
        return GroupSetting()


add_creator(GroupSettingClassCreator)
