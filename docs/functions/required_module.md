# 必要模块

本篇为必要模块，请勿删除

> ## 关于

模块位置：`modules.required.about`

模块用途：显示一些关于bot的信息

使用方法：在群中发送 `/关于`，`/about` 即可

> ## 后端api

模块位置：`modules.required.backend_api`

模块用途：用于管理面板的接入

使用方法：无

> ## 聊天记录器

模块位置：`modules.required.chat_recorder`

对聊天记录进行存储，可配合词云等插件使用

使用方法：自动触发

> ## bot管理

模块位置：`modules.required.command`

一个执行管理命令的插件

使用方法：

- 在群中发送 `/setting -set [-g] func=value` 可[全局]更改设置值
- 在群中发送 `/blacklist -add/-remove/-clear [-g] {target(At/int)}` 可[全局]添加/移除/清空对应目标黑名单
- 在群中发送 `/user -grant [-g] -l={level}` 可[全局]更改群员权限

> ## 错误报告

模块位置：`modules.required.exception_catcher`

一个向主人报告错误的插件

使用方法：自动触发

> ## 群成员备份

模块位置：`modules.required.group_member_backup`

一个备份群成员的插件

使用方法：

- 发送 `/群成员备份` 对当前群进行备份
- 发送 `/群成员备份 -s -g={qq群号}` 查看对应qq群备份信息

> ## 帮助

模块位置：`modules.required.helper`

一个提供帮助的插件

使用方法：
- 发送 `/help` 即可查看所有插件
- 发送 `/help {index}` 即可查看插件详细信息

> ## 消息自助撤回

模块位置：`modules.required.message_revoke`

一个可以自动撤回之前发送消息的插件

使用方法：回复 `撤回` 即可撤回回复的消息（Bot发出的，如果是管理员也可撤回普通成员消息）

> ## 事件处理

模块位置：`modules.required.mirai_events`

一个对不同事件进行处理的插件

使用方法：自动触发

配置：可通过模块包下的 `events_config.json` 进行自定义回复，请按照文件中格式进行修改

```json5
{
  "MemberLeaveEventQuit": "用户离开",
  "MemberMuteEvent":  "用户被禁言",
  "MemberUnmuteEvent": "用户被解除禁言",
  "MemberLeaveEventKick": "用户被踢",
  "MemberSpecialTitleChangeEvent": "用户群头衔改变",
  "MemberPermissionChangeEvent": "用户群权限改变",
  "BotLeaveEventKick": "bot被踢",
  "GroupNameChangeEvent": "群名改变",
  "GroupEntranceAnnouncementChangeEvent": "入群公告改变",
  "GroupAllowAnonymousChatEvent": {
    "open": "匿名功能开启",
    "close": "匿名功能关闭"
  },
  "GroupAllowConfessTalkEvent": {
    "open": "坦白说功能开启",
    "close": "坦白说功能关闭"
  },
  "GroupAllowMemberInviteEvent": {
    "open": "允许邀请成员加入",
    "close": "不允许邀请成员加入"
  },
  "MemberCardChangeEvent": "群名片变更",
  "NewFriendRequestEvent": "新好友申请",
  "MemberJoinRequestEvent": "新加群请求",
  "BotInvitedJoinGroupRequestEvent": "bot被邀请进群",
  "BotJoinGroupEvent": "bot入群",
  "MemberHonorChangeEvent": {
    "achieve": "用户获得荣誉",
    "lose": "用户失去荣誉"
  },
  "MemberJoinEvent": "新用户入群"
}
```

> ## 插件管理

bot管理插件

模块位置：`modules.required.saya_manager`

使用方法：

- 发送 `已加载插件` 查看已加载插件
- 发送 `未加载插件` 查看未加载插件
- 发送 `加载插件 [编号|名称]` 可加载插件
- 发送 `重载插件 [编号|名称]` 可重载插件
- 发送 `卸载插件 [编号|名称]` 可卸载插件
- 发送 `打开插件 [编号|名称]` 可打开插件
- 发送 `关闭插件 [编号|名称]` 可关闭插件
- 编号可从 `已加载插件` 或 `未加载插件` 命令获取

> ## 系统状态

一个可以查看系统状态的插件

模块位置：`modules.required.system_status`

使用方法：

- 发送 `/sys` 或 `/sys -a` 或 `/sys -all` 查看CPU、内存以及图库占用信息
- 发送 `/sys -i` 或 `/sys -info` 查看CPU、内存信息
- 发送 `/sys -s` 或 `/sys -storage` 查看图库占用信息