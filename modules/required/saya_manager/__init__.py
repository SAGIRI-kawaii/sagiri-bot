import asyncio

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Image, Source
from graia.ariadne.event.message import Member, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, RegexMatch, RegexResult, UnionMatch

from .utils import *
from shared.models.saya_data import SayaData
from shared.utils.waiter import ConfirmWaiter
from shared.models.types import ModuleOperationType
from shared.models.config import load_plugin_meta_by_module
from shared.utils.UI import ColumnList, ColumnListItem, ColumnListItemSwitch, GenForm, Column, one_mock_gen, ColumnTitle
from shared.utils.control import (
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute,
    Permission
)

saya = create(Saya)
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
saya_data = create(SayaData)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("已加载插件")])],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def show_installed_module(app: Ariadne, group: Group):
    modules = [ColumnTitle(title="发送 '卸载/重载插件 {编号}' 来卸载/重载对应插件")]
    for i, c in enumerate(saya.channels):
        plugin_meta = load_plugin_meta_by_module(c)
        modules.append(
            ColumnList(rows=[
                ColumnListItem(
                    subtitle=f"{i + 1}. {plugin_meta.display_name or saya.channels[c].meta['name'] or c.split('.')[-1]}",
                    content=c,
                    right_element=ColumnListItemSwitch(switch=saya_is_turned_on(c, group))
                )
            ])
        )
    form = GenForm(columns=[Column(elements=modules[i: i + 20]) for i in range(0, len(modules), 20)])
    await app.send_message(group, MessageChain(Image(data_bytes=await one_mock_gen(form))))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("未加载插件")])],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            Permission.require(Permission.SUPER_ADMIN)
        ]
    )
)
async def show_not_installed_module(app: Ariadne, group: Group):
    not_installed_module = get_not_installed_channels()
    if not not_installed_module:
        return await app.send_message(group, MessageChain("没有未加载的插件呢！"))
    modules = [ColumnTitle(title="发送 '加载插件 {编号}' 来加载对应插件")]
    for i, c in enumerate(not_installed_module):
        plugin_meta = load_plugin_meta_by_module(c)
        modules.append(
            ColumnList(rows=[
                ColumnListItem(
                    subtitle=f"{i + 1}. {plugin_meta.display_name or c.split('.')[-1]}",
                    content=c
                )
            ])
        )
    form = GenForm(columns=[Column(elements=modules[i: i + 20]) for i in range(0, len(modules), 20)])
    await app.send_message(group, MessageChain(Image(data_bytes=await one_mock_gen(form))))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("加载", "卸载", "重载") @ "operation",
                FullMatch("插件"),
                RegexMatch("[0-9]+") @ "number"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            Permission.require(Permission.SUPER_ADMIN)
        ]
    )
)
async def module_operation(
    app: Ariadne, group: Group, member: Member, source: Source, operation: RegexResult, number: RegexResult
):
    operation = operation.result.display
    number = int(number.result.display)
    if operation == "加载":
        modules = get_not_installed_channels()
        operation_type = ModuleOperationType.INSTALL
    else:
        modules = get_installed_channels()
        operation_type = ModuleOperationType.UNINSTALL if operation == "卸载" else ModuleOperationType.RELOAD
    if number == 0 or number > len(modules):
        return await app.send_message(group, MessageChain(f"没有这个编号呢~目前只有{len(modules)}个插件诶~"))
    module = modules[number - 1]
    await app.send_message(group, MessageChain(f"你确定要{operation}插件 `{module}` 吗？（是/否）"))
    try:
        if await asyncio.wait_for(inc.wait(ConfirmWaiter(group, member)), 30):
            exceptions = core.module_operation(module, operation_type)
            if exceptions:
                return await app.send_group_message(
                    group,
                    MessageChain("\n".join(f"模块 <{m}> {operation}发生错误：{e}" for m, e in exceptions.items())),
                    quote=source
                )
            return await app.send_group_message(group, MessageChain(f"模块：{module} {operation}完成"), quote=source)
    except asyncio.TimeoutError:
        return await app.send_group_message(group, MessageChain("回复等待超时，进程退出"), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                UnionMatch("打开", "关闭") @ "operation",
                FullMatch("插件"),
                RegexMatch(r"[\w]+") @ "module"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            Permission.require(Permission.SUPER_ADMIN)
        ]
    )
)
async def module_switch(app: Ariadne, group: Group, source: Source, operation: RegexResult, module: RegexResult):
    operation = operation.result.display
    module = module.result.display
    modules = list(saya.channels.keys())
    if module.isdigit():
        if not 0 <= int(module) - 1 < len(modules):
            return await app.send_group_message(
                group, MessageChain(f"没有这个编号呢~目前只有{len(modules)}个插件诶~"), quote=source
            )
        target_module = modules[int(module) - 1]
    else:
        target_module = next((c for c in saya.channels.keys() if saya.channels[c].meta["name"] == module), None)
        if not target_module:
            return await app.send_group_message(
                group, MessageChain(f"没有插件 {module} 诶~再检查一下？"), quote=source
            )
    saya_data.switch_on(target_module, group) if operation == "打开" else saya_data.switch_off(target_module, group)
    await app.send_group_message(
        group,
        MessageChain(f"插件 {target_module} 已{operation}！"),
        quote=source,
    )
