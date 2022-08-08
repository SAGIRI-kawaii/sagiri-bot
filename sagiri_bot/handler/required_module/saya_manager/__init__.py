import os
import re
from typing import List, Dict, Optional, Union

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Plain, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage

from .utils import saya_data
from sagiri_bot.internal_utils import MessageChainUtils
from sagiri_bot.internal_utils import user_permission_require

saya = Saya.current()
channel = Channel.current()

channel.name("SayaManager")
channel.author("SAGIRI-kawaii")
channel.description(
    "插件管理插件"
    "发送 `已加载插件` 查看已加载插件\n"
    "发送 `插件详情 [编号|名称]` 可查看插件详情\n"
    "发送 `[加载|重载|卸载|打开|关闭]插件 [编号|名称]` 可加载/重载/卸载/打开/关闭插件"
)

inc = InterruptControl(saya.broadcast)


def get_loaded_channels() -> Dict[str, Channel]:
    return saya.channels


def get_all_channels() -> List[str]:
    ignore = ["__init__.py", "__pycache__"]
    dirs = [
        "modules",
        "sagiri_bot/handler/required_module",
        "sagiri_bot/handler/handlers",
    ]
    modules = []
    for path in dirs:
        for module in os.listdir(path):
            if module in ignore:
                continue
            if os.path.isdir(module):
                modules.append(f"{path.replace('/', '.')}.{module}")
            else:
                modules.append(f"{path.replace('/', '.')}.{module.split('.')[0]}")
    return modules


def get_unloaded_channels() -> List[str]:
    loaded_channels = get_loaded_channels()
    all_channels = get_all_channels()
    return [channel for channel in all_channels if channel not in loaded_channels]


def get_channel(name: str) -> Optional[Channel]:
    return get_loaded_channels().get(name)


def load_channel(modules: Union[str, List[str]]) -> Dict[str, Exception]:
    ignore = ["__init__.py", "__pycache__"]
    exceptions = {}
    if isinstance(modules, str):
        modules = [modules]
    with saya.module_context():
        for module in modules:
            if module in ignore:
                continue
            try:
                saya.require(module)
            except Exception as e:
                exceptions[module] = e
    return exceptions


def unload_channel(modules: Union[str, List[str]]) -> Dict[str, Exception]:
    exceptions = {}
    if isinstance(modules, str):
        modules = [modules]
    loaded_channels = get_loaded_channels()
    channels_to_unload = {
        module: loaded_channels[module]
        for module in modules
        if module in loaded_channels
    }
    with saya.module_context():
        for channel, value in channels_to_unload.items():
            try:
                saya.uninstall_channel(value)
            except Exception as e:
                exceptions[channel] = e
    return exceptions


def reload_channel(modules: Union[str, List[str]]) -> Dict[str, Exception]:
    exceptions = {}
    if isinstance(modules, str):
        modules = [modules]
    loaded_channels = get_loaded_channels()
    channels_to_reload = {
        module: loaded_channels[module]
        for module in modules
        if module in loaded_channels
    }
    with saya.module_context():
        for channel, value in channels_to_reload.items():
            try:
                saya.reload_channel(value)
            except Exception as e:
                exceptions[channel] = e
    return exceptions


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def saya_manager(
    app: Ariadne, message: MessageChain, group: Group, member: Member, source: Source
):
    if message.display.strip() == "已加载插件":
        loaded_channels = get_loaded_channels()
        keys = sorted(loaded_channels.keys())
        return await app.send_group_message(
            group,
            await MessageChainUtils.messagechain_to_img(
                MessageChain(
                    [Plain(text="目前加载插件：\n")]
                    + [
                        Plain(
                            text=f"{i + 1}. {_channel.meta['name'] or _channel.module.split('.')[-1]}\n"
                        )
                        for i in range(len(keys))
                        if (_channel := loaded_channels[keys[i]])
                    ]
                    + [Plain(text="发送 `插件详情 [编号|名称]` 可查看插件详情")]
                )
            ),
        )
    elif re.match(r"插件详情 .+", message.display):
        target = message.display[5:].strip()
        loaded_channels = get_loaded_channels()
        keys = list(loaded_channels.keys())
        if target.isdigit():
            keys.sort()
            if not 0 <= int(target) - 1 < len(keys):
                return await app.send_group_message(
                    group, MessageChain("错误的编号！请检查后再发送！"), quote=source
                )
            channel = loaded_channels[keys[int(target) - 1]]
            channel_path = keys[int(target) - 1]
        else:
            for lchannel in loaded_channels.keys():
                if loaded_channels[lchannel]._name == target:
                    channel = loaded_channels[lchannel]
                    channel_path = lchannel
                    break
            else:
                return await app.send_group_message(
                    group, MessageChain("错误的名称！请检查后再发送！"), quote=source
                )
        return await app.send_group_message(
            group,
            MessageChain(
                [
                    Plain(text=f"插件名称：{channel._name}\n"),
                    Plain(text=f"插件作者：{'、'.join(channel._author)}\n"),
                    Plain(text=f"插件描述：{channel._description}\n"),
                    Plain(text=f"插件包名：{channel_path}"),
                ]
            ),
            quote=source,
        )
    elif message.display == "未加载插件":
        if not await user_permission_require(group, member, 3):
            return await app.send_group_message(
                group, MessageChain("爬，权限不足"), quote=source
            )
        unloaded_channels = get_unloaded_channels()
        unloaded_channels.sort()
        return await app.send_group_message(
            group,
            MessageChain(
                [Plain(text="目前未加载插件：\n")]
                + [
                    Plain(text=f"{i + 1}. {unloaded_channels[i]}\n")
                    for i in range(len(unloaded_channels))
                ]
                + [Plain(text="发送 `[加载|卸载|重载]插件 [编号|名称]` 可加载/卸载/重载插件\n")]
            ),
            quote=source,
        )
    elif re.match(r"加载插件 .+", message.display):
        if not await user_permission_require(group, member, 3):
            return await app.send_group_message(
                group, MessageChain("爬，权限不足"), quote=source
            )
        target = message.display[5:].strip()
        unloaded_channels = get_unloaded_channels()
        if target.isdigit():
            unloaded_channels.sort()
            if not 0 <= int(target) - 1 < len(unloaded_channels):
                return await app.send_group_message(
                    group, MessageChain("错误的编号！请检查后再发送！"), quote=source
                )
            channel = unloaded_channels[int(target) - 1]
        else:
            for ulchannel in unloaded_channels:
                if ulchannel == target:
                    channel = ulchannel
                    break
            else:
                return await app.send_group_message(
                    group, MessageChain("错误的名称！请检查后再发送！"), quote=source
                )

        await app.send_message(group, MessageChain(f"你确定要加载插件 `{channel}` 吗？（是/否）"))

        @Waiter.create_using_function([GroupMessage])
        def confirm_waiter(
            waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
        ):
            if all([waiter_group.id == group.id, waiter_member.id == member.id]):
                if re.match(r"[是否]", waiter_message.display):
                    return waiter_message.display
                else:
                    return ""

        result = await inc.wait(confirm_waiter)
        if not result:
            return await app.send_group_message(
                group, MessageChain("非预期回复，进程退出"), quote=source
            )
        elif result == "是":
            result = load_channel(channel)
            if result:
                return await app.send_group_message(
                    group, MessageChain(f"发生错误：{result[channel]}"), quote=source
                )
            else:
                return await app.send_group_message(
                    group, MessageChain("加载成功"), quote=source
                )
        else:
            return await app.send_group_message(
                group, MessageChain("进程退出"), quote=source
            )
    elif re.match(r"[卸重]载插件 .+", message.display):
        if not await user_permission_require(group, member, 3):
            return await app.send_group_message(
                group, MessageChain("爬，权限不足"), quote=source
            )
        load_type = "reload" if message.display[0] == "重" else "unload"
        target = message.display[5:].strip()
        loaded_channels = get_loaded_channels()
        keys = sorted(loaded_channels.keys())
        if target.isdigit():
            if not 0 <= int(target) - 1 < len(keys):
                return await app.send_group_message(
                    group, MessageChain("错误的编号！请检查后再发送！"), quote=source
                )
            channel = loaded_channels[keys[int(target) - 1]]
            channel_path = keys[int(target) - 1]
        else:
            for lchannel in loaded_channels.keys():
                if loaded_channels[lchannel]._name == target:
                    channel = loaded_channels[lchannel]
                    channel_path = lchannel
                    break
            else:
                return await app.send_group_message(
                    group, MessageChain("错误的名称！请检查后再发送！"), quote=source
                )

        await app.send_message(
            group,
            MessageChain(f"你确定要{message.display[0]}载插件 `{channel._name}` 吗？（是/否）"),
        )

        @Waiter.create_using_function([GroupMessage])
        def confirm_waiter(
            waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
        ):
            if all([waiter_group.id == group.id, waiter_member.id == member.id]):
                if re.match(r"[是否]", waiter_message.display):
                    return waiter_message.display
                else:
                    return ""

        result = await inc.wait(confirm_waiter)
        if not result:
            return await app.send_group_message(
                group, MessageChain("非预期回复，进程退出"), quote=source
            )
        elif result == "是":
            result = (
                unload_channel(channel_path)
                if load_type == "unload"
                else reload_channel(channel_path)
            )
            if result:
                return await app.send_group_message(
                    group, MessageChain(f"发生错误：{result[channel_path]}"), quote=source
                )
            else:
                return await app.send_group_message(
                    group, MessageChain(f"{message.display[0]}载成功"), quote=source
                )
        else:
            return await app.send_group_message(
                group, MessageChain("进程退出"), quote=source
            )
    elif re.match(r"(打开|关闭)插件 .+", message.display):
        if not await user_permission_require(group, member, 3):
            return await app.send_group_message(
                group, MessageChain("爬，权限不足"), quote=source
            )
        switch_type = "on" if message.display[:2] == "打开" else "off"
        target = message.display[5:].strip()
        loaded_channels = get_loaded_channels()
        keys = sorted(loaded_channels.keys())
        channel_path = ""
        if target.isdigit():
            if not 0 <= int(target) - 1 < len(keys):
                return await app.send_group_message(
                    group, MessageChain("错误的编号！请检查后再发送！"), quote=source
                )
            channel_path = keys[int(target) - 1]
        else:
            for lchannel in loaded_channels.keys():
                if loaded_channels[lchannel]._name == target:
                    channel_path = lchannel
                    break
        saya_data.switch_on(
            channel_path, group
        ) if switch_type == "on" else saya_data.switch_off(channel_path, group)
        return await app.send_group_message(
            group,
            MessageChain(f"插件{channel_path}已{message.display[:2]}！"),
            quote=source,
        )
