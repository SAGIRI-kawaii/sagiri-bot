# 管理

> ## 群组内管理 

注：设置命令通用格式：`setting -set {command}={new_value}` 其中`command` 为命令名称，`new_value` 为要设置的状态，支持多命令同时执行

使用示例： `setting -set setu=True real=True bizhi=True ...`

| 名称 | 描述 | command | 合法value             | 所需权限等级 | 备注 |
| ------------ | ------------ | ------------ |---------------------| ------------ | --- |
| 频率限制 | 限制群内功能使用频率防止机器人负载过高崩溃 | frequency_limit | True/False | 2+ |  |
| 反撤回功能开关 | 决定bot是否对本群消息进行相应 | anti_revoke | True/False | 2+ |  |
| 闪照转换功能开关 | 决定bot是否对本群闪照进行转换 | anti_flash_image | True/False | 2+ |  |
| 上线提醒 | 机器人上线自动发送上班消息 | online_notice | True/False | 2+ |  |
| 每日新闻 | 是否开放每日新闻 | daily_newspaper | True/False | 2+ |  |
| 群内开关 | 决定bot是否对本群消息进行相应 | switch | True/False | 3+ |  |
| R-18 | 是否开放R-18 | r18 | True/False | 3+ | 仅控制setu图库 |
| R-18处理方式 | 对发送的R-18图片做撤回/闪照处理 | r18_process | revoke/flash/normal | 3+ | 仅在r18选项开启时起作用，后期可能会加入不作处理选项 |

> ## 权限授予

在重构后，SAGIRI-BOT引入了权限等级的概念，权限等级的定义如下：

| 权限等级 | 等级    |
|------|-------|
| 1    | 普通用户  |
| 2    | 管理员   |
| 3    | 超级管理员 |
| 4    | 所有者   |

若想对其他账户进行等级授权，你应至少达到权限等级3+

对用户进行授权请使用 `/user -grant @member [1-3]` 命令，其中授权3级权限需要账户拥有4级即所有者权限

被授权后的用户将可以使用文档内对应权限等级的管理命令

注：等级4的账户将在机器人初始化时就存入数据库，对应成员id为 `config.yaml` 中所填入的 `bot_qq` 项

> ## 黑名单相关

- 加入黑名单：`/blacklist -add @member`
- 移除黑名单：`/blacklist -remove @member`
- 注：权限要求2+
