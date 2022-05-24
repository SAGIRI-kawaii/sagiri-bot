# 必要模块

本篇为必要模块，请勿删除

> ## MiraiEvent

模块位置：`sagiri_bot.handler.required_module.mirai_event`

对获取到的各种群事件进行响应

使用方法：自动触发

可自行添加没有的事件

添加方式：在 `mirai_event.mirai_events.py` 中添加异步函数，函数名为目标事件的下划线命名方式

例如对于事件 `MemberLeaveEventKick`，可定义函数如下：
`async def member_leave_event_kick(app: Ariadne, group: Group, event: MemberLeaveEventKick): ...`

> ## SayaManager

对所有已加载插件进行管理

模块位置：`sagiri_bot.handler.required_module.saya_manager`

使用方法：

- 发送 `已加载插件` 查看已加载插件
- 发送 `插件详情 [编号|名称]` 可查看插件详情
- 发送 `[加载|重载|卸载|打开|关闭]插件 [编号|名称]` 可加载/重载/卸载/打开/关闭插件

工作原理：

通过 `Saya.channels` 获取所有已加载插件，通过 `Cube` 获取 `Listener` 并移除，将 `manageable` 加入 `channel.decorators` 并重新注册 `Listener`，并在其中标注插件 `module` 以将插件和 `Listener` 联系起来

注意：`saya_manager` 应为最后加载的插件，以保证能获取到所有加载的插件

> ## BotManagement

bot管理插件

模块位置：`sagiri_bot.handler.required_module.bot_management`

使用方法：

- 发送 `setting -set key1=value1 key2=value2 ...` 改变群内设置
- 发送 `user -grant @target [1-3]` 改变成员权限等级
- 发送 `blacklist -add @target` 添加群内黑名单
- 发送 `blacklist -remove @target` 移除群内黑名单

> ## ChatRecorder

对聊天记录进行存储，可配合词云等插件使用

使用方法：自动触发

> ## SystemStatus

bot管理插件

模块位置：`sagiri_bot.handler.required_module.system_status`

使用方法：

- 发送 `/sys` 或 '/sys -a' 或 '/sys -all' 查看CPU、内存以及图库占用信息
- 发送 `/sys -i` 或 '/sys -info' 查看CPU、内存信息
- 发送 `/sys -s` 或 '/sys -storage' 查看图库占用信息