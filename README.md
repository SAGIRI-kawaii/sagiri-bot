# SAGIRI-BOT
基于 Mirai 和 Graia 的船新版本，~~是兄弟就来砍我~~

New version of sagiri-bot based on Mirai and Graia

## 目录
  * [目录](#目录)
  * [开始使用](#开始使用)
    + [使用前准备](#使用前准备)
    + [如何启动](#如何启动)
    + [参数说明](#参数说明)
      - [config.yaml](#configyaml)
  * [使用文档](#使用文档)
  * [注意](#注意)
  * [TODO](#todo)
  * [鸣谢](#鸣谢)

## 开始使用

### 使用前准备

不同于老版的SAGIRI-BOT，新版的SAGIRI-BOT使用了ORM框架，这意味着可以很方便的将项目适配各种不同的数据库

- 配置数据库链接
    - mysql: mysql+pymysql://username:password@localhost:3306/dbname
    - sqlite: sqlite:///filename.db
    - oracle: oracle://username:password@192.168.1.6:1521/dbname
- 下载 [mirai-console](https://github.com/mamoe/mirai-console) 并配置 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，这些都可以在 [mirai](https://github.com/mamoe/mirai) 项目中找到
- 若上一条不会配置，请考虑使用 [mirai-console-loader](https://github.com/iTXTech/mirai-console-loader) 加载器进行配置
- 打开 `configdemo.yaml`，配置好个人信息，并将文件更名为 `config.yaml`，配置说明见[config文件参数说明](#configyaml)

### 如何启动

首先，启动 mirai-console，确保其正常运行且插件正常安装
在文件夹下执行 `python main.py` 即可
你应当见到类似如下格式的信息：
```text
2021-04-11 20:21:53.776 | INFO     | SAGIRIBOT.Core.AppCore:__init__:39 - Initializing
2021-04-11 20:21:53.818 | INFO     | SAGIRIBOT.Core.AppCore:__init__:58 - Initialize end
2021-04-11 20:21:53.819 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> ChatRecordHandler
2021-04-11 20:21:55.765 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> BotManagementHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> StatusPresenterHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> ImageSenderHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> TrendingHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> StylePictureGeneraterHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> AvatarFunPicHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> AbbreviatedPredictionHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> LeetcodeInfoHanlder
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> QrCodeGeneratorHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> ImageSearchHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> BiliBiliBangumiScheduleHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> TodayInHistoryHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> BilibiliAppParserHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> PhantomTankHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> SteamGameInfoSearchHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> MarketingContentGeneratorHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> NetworkCompilerHandler
2021-04-11 20:21:55.766 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> BangumiInfoSearchHandler
2021-04-11 20:21:55.767 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> LatexGeneratorHandler
2021-04-11 20:21:55.767 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> JLUCSWNoticeHandler
2021-04-11 20:21:55.767 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> GroupWordCloudGeneratorHandler
2021-04-11 20:21:55.767 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> KeywordReplyHandler
2021-04-11 20:21:55.767 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> ChatReplyHandler
2021-04-11 20:21:55.767 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> RepeaterHandler
2021-04-11 20:21:55.767 | INFO     | SAGIRIBOT.Handler.Handler:__init__:33 - Create handler -> HeadHandler
2021-04-11 20:21:55.770 | SUCCESS  | SAGIRIBOT.Handler.MessageHandler:__init__:50 - 
----------------------------------------------
职责链加载成功，目前链序：
ChatRecordHandler                       一个记录聊天记录的Handler
BotManagementHandler                    bot管理Handler
StatusPresenterHandler                  一个bot状态显示Handler
ImageSenderHandler                      一个可以发送图片的Handler
TrendingHandler                         一个获取热搜的Handler
StylePictureGeneraterHandler            一个可以生成风格图片的Handler
AvatarFunPicHandler                     一个可以生成头像相关趣味图的Handler
AbbreviatedPredictionHandler            一个获取英文缩写意思的Handler
LeetcodeInfoHanlder                     一个可以获取Leetcode信息的Handler
QrCodeGeneratorHandler                  一个生成二维码的Handler
ImageSearchHandler                      一个可以搜索Pixiv图片的Handler
BiliBiliBangumiScheduleHandler          一个可以获取BiliBili7日内新番时间表的Handler
TodayInHistoryHandler                   一个获取历史上的今天的Handler
BilibiliAppParserHandler                一个可以解析BiliBili小程序的Handler
PhantomTankHandler                      一个幻影坦克生成器Handler
SteamGameInfoSearchHandler              一个可以搜索steam游戏信息的Handler
MarketingContentGeneratorHandler        一个营销号生成器Handler
NetworkCompilerHandler                  一个网络编译器Handler
BangumiInfoSearchHandler                一个可以搜索番剧信息的Handler
LatexGeneratorHandler                   一个latex公式转图片的Handler
JLUCSWNoticeHandler                     一个可以获取吉林大学软件学院教务通知的Handler
GroupWordCloudGeneratorHandler          群词云生成器
KeywordReplyHandler                     一个关键字回复Handler
ChatReplyHandler                        一个可以自定义/。智能回复的Handler
RepeaterHandler                         一个复读Handler
----------------------------------------------
[2021-04-11 20:21:55,770][INFO]: initializing app...
[2021-04-11 20:21:55,778][INFO]: detecting remote's version...
[2021-04-11 20:21:55,786][INFO]: detected remote's version: 1.9.8
[2021-04-11 20:21:55,789][INFO]: using pure websocket to receive event
[2021-04-11 20:21:55,789][INFO]: found websocket disabled, so it has been enabled.
2021-04-11 20:21:55.898 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:121 - 本次启动活动群组如下：
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
2021-04-11 20:21:55.899 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:123 - 群ID: 123456789     群名: XXXXXX
[2021-04-11 20:21:55,923][INFO]: event receive method checked.
[2021-04-11 20:21:55,923][INFO]: this application's initialization has been completed.
[2021-04-11 20:21:55,923][INFO]: --- setting start ---
[2021-04-11 20:21:55,923][INFO]: broadcast using: <graia.broadcast.Broadcast object at 0x0000022E748E7790>
[2021-04-11 20:21:55,923][INFO]: enable log of chat: no
[2021-04-11 20:21:55,923][INFO]: debug: no
[2021-04-11 20:21:55,923][INFO]: version(remote): 1.9.8
[2021-04-11 20:21:55,923][INFO]: --- setting end ---
[2021-04-11 20:21:55,923][INFO]: application has been initialized, used 0.153s
[2021-04-11 20:21:55,924][INFO]: websocket daemon: websocket connection starting...
[2021-04-11 20:21:55,925][INFO]: websocket: connected
[2021-04-11 20:21:55,925][INFO]: websocket: ping task created
```
现在，来试一试你的机器人吧！

### 参数说明

#### config.yaml
用于存储机器人的各种配置，可随时进行更改
注意：所有路径的结尾都应该有斜杠，如："/bot/setuPath/" 或 "\bot\setuPath\" 等

|  参数名   | 说明  |
|  ----  | ----  |
| BotQQ  | 机器人的QQ号 |
| HostQQ  | 主人的QQ号，默认权限等级4 |
| authKey | mirai-api-http 的 authKey，格式为 `!!str authKey` |
| miraiHost | 主机ip + mirai-api-http 的 port，一般在本地不用更改 |
| DBLink | 数据库链接，可参看 [使用前准备](#使用前准备) |
| setuPath | 正常二次元图片存储路径（绝对路径） |
| setu18Path | 不对劲二次元图片存储路径（绝对路径） |
| realPath | 三次元图片存储路径（绝对路径） |
| realHighqPath | 高质量三次元图片存储路径（绝对路径） |
| wallpaperPath | 壁纸图片存储路径（绝对路径） |
| sketchPath | 线稿图片存储路径（绝对路径） |
| txAppId | 腾讯AI开放平台AppId（自行申请），格式为 `!!str txAppId` |
| txAppKey | 腾讯AI开放平台AppKey（自行申请） |
| shadiaoAppName | shadiaoApp 应用名（自行申请） |
| saucenaoCookie | saucenao cookie（自行登录获取） |
| webManagerApi | api是否启动（用于管理页面） |
| webManagerAutoBoot | 是否自动打开管理页面（webManagerApi为True时才起作用） |
| errorRetention | 错误日志记录周期 |
| commonRetention | 普通日志清空周期 |

## 使用文档

- [功能列表](docs/functions.md)
- [管理](docs/manage.md)

因项目重构，原文档失效，新文档还在完善中🕊🕊🕊

## 项目特性

- 使用简单的前端管理器

## 注意
目前机器人尚未完善，仍有许多bug存在，若您在使用中发现了bug或有更好的建议，请提ISSUE
```diff
- 特别注意：机器人中有许多功能使用的是我的私用API，可能会随时修改或关闭，请及时寻找替代用API，因API改动造成的程序错误概不负责
```

## TODO
- [x] 添加并完善日志记录功能
- [x] 支持Saya加载插件
- [ ] 可视化管理页面
- [ ] 完善文档
- [ ] 点歌功能
- [ ] 支持发送语音
- [ ] 广告识别功能（自动禁言、撤回、移除）

## 鸣谢
- [mirai](https://github.com/mamoe/mirai) ，高效率 QQ 机器人框架 / High-performance bot framework for Tencent QQ

- [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，Mirai HTTP API (console) plugin

- [Graia Appliation](https://github.com/GraiaProject/Application) ，一个设计精巧, 协议实现完备的, 基于 mirai-api-http 的即时聊天软件自动化框架.

