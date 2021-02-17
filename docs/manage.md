# 群组管理

注：设置命令通用格式：`@bot setting.command.newState` 其中`@bot`为At机器人，command为命令名称，newState为要设置的状态

| 名称 | 描述 | command | 支持的newState | 备注 |
| ------------ | ------------ | ------------ | ------------ | ------------ |
| 复读  | 控制群内自动复读 | repeat | Enable/Disable |   |
| 频率限制 | 限制群内功能使用频率防止机器人负载过高崩溃 | countLimit | Enable/Disable | 默认为10秒内允许最大总权重为10 |
| 二次元图片 | 是否开放二次元图片功能 | setu | Enable/Disable |   |
| 三次元图片 | 是否开放三次元图片功能 | real | Enable/Disable | 控制real、realHighq两个图库 |
| 壁纸 | 是否开放壁纸功能 | bizhi | Enable/Disable |   |
| R-18 | 是否开放R-18 | r18 | Enable/Disable | 仅控制setu图库 |
| pixiv以图搜图 | 是否开放pixiv以图搜图功能 | search | Enable/Disable |   |
| 图片鉴黄 | 是否开放图片鉴黄功能  | yellowPredict  | Enable/Disable |   |
| 番剧名搜索 | 是否开放番剧名搜索功能 | searchBangumi  | Enable/Disable |   |
| debug | 显示每个请求所执行的时间（从收到消息到发送） | debug | Enable/Disable |  |
| 成就系统 | 决定bot是否发布新成就达成消息通知 | achievement | Enable/Disable |  |
| 网络编译器 | 菜鸟教程网络编译器开关 | compile | Enable/Disable |  |
| 上线提醒 | 机器人上线自动发送上班消息 | onlineNotice | Enable/Disable |  |
| 长文本形式 | 控制长文本是以图片还是文字方式发出 | longTextType | img/text | 长文本发送过多可能会被tx风控 |
| R-18处理方式 | 对发送的R-18图片做撤回/闪照处理 | r18Process  | revoke/flashImage | 仅在r18选项开启时起作用，后期可能会加入不作处理选项 |
| 回复方式 | 决定bot被@时的反应 | speakMode  | normal/rainbow/zuanLow/zuanHigh/chat | 请慎用zuanLow 和 zuanHigh模式 |
| 点歌平台 | 决定点歌功能的平台及开关 | music | off/wyy | 目前只支持网易云平台 |
| 群内开关 | 决定bot是否对本群消息进行相应 | switch | on/off |  |