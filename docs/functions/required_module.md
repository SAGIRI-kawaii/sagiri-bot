# 必要模块

本篇为必要模块，请勿删除
 
> ## 关于（About）

一些关于bot的信息

模块位置：`modules.required.about`

模块版本：`0.1`

使用方法：

- 在群中发送 `关于` 即可

使用示例：

- `关于`

触发前缀：`about`、`关于`、`/about`、`/关于`

可用性：可用

> ## 管理面板后端API（BackendAPI）

为管理面板提供接入bot的api

模块位置：`modules.required.backend_api`

模块版本：`0.1`

使用方法：

- 暂无

使用示例：

- 暂无

触发前缀：

可用性：可用

> ## 群聊记录存储（ChatRecorder）

一个对聊天记录进行存储的插件，可配合词云等插件使用

模块位置：`modules.required.chat_recorder`

模块版本：`0.1`

使用方法：

- 自动触发

使用示例：

- 暂无

触发前缀：

可用性：可用

> ## 管理命令模块（Command）

一个执行管理命令的插件

模块位置：`modules.required.command`

模块版本：`0.1`

使用方法：

- 在群中发送 /setting -set [-g] func=value 可[全局]更改设置值
- 在群中发送 /blacklist -add/-remove/-clear [-g] {target(At/int)} 可[全局]添加/移除/清空对应目标黑名单
- 在群中发送 /user -grant [-g] -l={level} 可[全局]更改群员权限

使用示例：

- `全局关闭：/setting -set -g switch=False`
- `本群关闭：/setting -set switch=False`
- `全局黑名单：/blacklist -add -g @坏蛋`
- `本群黑名单：/blacklist -add @坏蛋`
- `清空黑名单：/blacklist -clear @坏蛋`
- `全局授权：/user -grant -g -l=2 @目标`
- `本群授权：/user -grant -l=2 @目标`

触发前缀：`/setting`

可用性：可用

> ## 错误报告（ExceptionCatcher）

一个向主人报告错误的插件

模块位置：`modules.required.exception_catcher`

模块版本：`0.1`

使用方法：

- 后台发生错误时自动触发

使用示例：

- 暂无

触发前缀：

可用性：可用

> ## 群成员备份（GroupMemberBackup）

一个备份群成员的插件

模块位置：`modules.required.group_member_backup`

模块版本：`0.1`

使用方法：

- 发送 `/群成员备份` 对当前群进行备份
- 发送 `/群成员备份 -s -g={qq群号}` 查看对应qq群备份信息

使用示例：

- `/群成员备份`
- `/群成员备份 -s -g=114514`

触发前缀：`群成员备份`、`/群成员备份`

可用性：可用

> ## 帮助模块（Helper）

一个提供帮助的插件

模块位置：`modules.required.helper`

模块版本：`0.2`

使用方法：

- 发送 `/help` 即可查看所有插件

使用示例：

- `查看所有插件：/help`
- `查看编号为27的插件：/help 27`

触发前缀：`help`、`菜单`、`纱雾帮助`、`帮助捏`、`帮助`、`功能`、`menu`、`.help`、`.菜单`、`.纱雾帮助`、`.帮助捏`、`.帮助`、`.功能`、`.menu`、`/help`、`/菜单`、`/纱雾帮助`、`/帮助捏`、`/帮助`、`/功能`、`/menu`、`#help`、`#菜单`、`#纱雾帮助`、`#帮助捏`、`#帮助`、`#功能`、`#menu`

可用性：可用

> ## 消息自助撤回（MessageRevoke）

一个可以自动撤回之前发送消息的插件

模块位置：`modules.required.message_revoke`

模块版本：`0.1`

使用方法：

- 回复 `撤回` 即可撤回回复的消息（Bot发出的，如果是管理员也可撤回普通成员消息）

使用示例：

- 暂无

触发前缀：`撤回`、`revoke`、`.撤回`、`.revoke`、`/撤回`、`/revoke`、`#撤回`、`#revoke`

可用性：可用

> ## 事件处理（MiraiEvents）

一个对不同事件进行处理的插件

模块位置：`modules.required.mirai_events`

模块版本：`0.2`

使用方法：

- 自动触发

使用示例：

- 暂无

触发前缀：

可用性：可用

!!! info "配置相关"
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

> ## 插件管理（SayaManager）

一个可以管理saya模块的插件

模块位置：`modules.required.saya_manager`

模块版本：`0.2`

使用方法：

- 发送 `已加载插件` 查看已加载插件
- 发送 `未加载插件` 查看未加载插件
- 发送 `加载插件 [编号|名称]` 可加载插件
- 发送 `重载插件 [编号|名称]` 可重载插件
- 发送 `卸载插件 [编号|名称]` 可卸载插件
- 发送 `打开插件 [编号|名称]` 可打开插件
- 发送 `关闭插件 [编号|名称]` 可关闭插件
- 编号可从 `已加载插件` 或 `未加载插件` 命令获取

使用示例：

- `加载插件 1`
- `加载插件 AbbreviatedPrediction`
- `卸载插件 AbbreviatedPrediction`
- `重载插件 1`
- `打开插件 AbbreviatedPrediction`
- `关闭插件 1`

触发前缀：

可用性：可用

> ## 系统状态（SystemStatus）

一个可以查看系统状态的插件

模块位置：`modules.required.system_status`

模块版本：`0.2`

使用方法：

- 发送 /sys 或 '/sys -a' 或 '/sys -all' 查看CPU、内存以及图库占用信息
- 发送 /sys -i 或 '/sys -info' 查看CPU、内存信息
- 发送 /sys -s 或 '/sys -storage' 查看图库占用信息

使用示例：

- 暂无

触发前缀：`/sys`、`/system`

可用性：可用