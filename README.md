<div align="center">
    <img width="160" src="docs/sagiri.jpg" alt="logo"></br>
    <h1>SAGIRI-BOT</h1>
</div>
    
----

<div align="center">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg"/>
    <img src="https://img.shields.io/badge/sqlalchemy-1.4.11+-orange.svg"/>
    <h3>一个基于 Mirai 和 Graia 的QQ机器人</h3>
    <div>SAGIRI之名取自动漫《埃罗芒阿老师》中的角色 <a href="https://zh.moegirl.org.cn/%E5%92%8C%E6%B3%89%E7%BA%B1%E9%9B%BE">和泉纱雾(Izumi Sagiri)</a></div>
    <br>
    <div>若您在使用过程中发现了bug或有一些建议，欢迎提出ISSUE或PR</div>
    <br>
    <div><s>来个star吧，球球惹！</s></div>
</div>



## 目录
  * [目录](#目录)
  * [项目特色](#项目特色)
  * [开始使用](#开始使用)
    + [使用前准备](#使用前准备)
    + [如何启动](#如何启动)
    + [参数说明](#参数说明)
      - [config.yaml](#configyaml)
  * [使用文档](#使用文档)
  * [注意](#注意)
  * [TODO](#todo)
  * [鸣谢](#鸣谢)

## 项目特色
- 基于Sqlalchemy的异步ORM
- 权限管理系统
- 频率限制模块
- 错误重发模块
- [丰富的功能](docs/functions.md)
- 可视化管理模块
- 基于loguru的日志系统

## 开始使用

### 使用前准备

不同于老版的SAGIRI-BOT，新版的SAGIRI-BOT使用了ORM框架，这意味着可以很方便的将项目适配各种不同的数据库

- 配置数据库链接
    - mysql: mysql+aiomysql://username:password@localhost:3306/dbname
    - sqlite: sqlite+aiosqlite:///filename.db
    - 注意：请自行安装对应的异步库，如aiomysql、aiosqlite等
- 下载 [mirai-console](https://github.com/mamoe/mirai-console) 并配置 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，这些都可以在 [mirai](https://github.com/mamoe/mirai) 项目中找到
- 若上一条不会配置，请考虑使用 [mirai-console-loader](https://github.com/iTXTech/mirai-console-loader) 加载器进行配置
- 打开 `configdemo.yaml`，配置好个人信息，并将文件更名为 `config.yaml`，配置说明见[config文件参数说明](#configyaml)
- 打开 `alembic.ini` ，将 `sqlalchemy.url` 更换为自己的连接（不要使用异步引擎否则会报错）

### 如何启动

首先，启动 mirai-console，确保其正常运行且插件正常安装
在文件夹下执行 `python main.py` 即可
你应当见到类似如下格式的信息：
```text
2021-05-15 10:51:39.006 | INFO     | SAGIRIBOT.Core.AppCore:__init__:44 - Initializing
2021-05-15 10:51:39.058 | INFO     | SAGIRIBOT.Core.AppCore:__init__:64 - Initialize end
2021-05-15 10:51:39.059 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.AbbreviatedPredictionHandler
2021-05-15 10:51:39.232 | INFO     | SAGIRIBOT.Handler.Handler:__init__:34 - Create handler -> ChatRecordHandler
2021-05-15 10:51:39.555 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.AbbreviatedPredictionHandler
2021-05-15 10:51:39.556 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.AbstractMessageTransformHandler
2021-05-15 10:51:39.556 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.AbstractMessageTransformHandler
2021-05-15 10:51:39.556 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.AvatarFunPicHandler
2021-05-15 10:51:39.556 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.AvatarFunPicHandler
2021-05-15 10:51:39.556 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.BangumiInfoSearchHandler
2021-05-15 10:51:39.556 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.BangumiInfoSearchHandler
2021-05-15 10:51:39.557 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.BangumiSearchHandler
2021-05-15 10:51:39.557 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.BangumiSearchHandler
2021-05-15 10:51:39.557 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.BilibiliAppParserHandler
2021-05-15 10:51:39.557 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.BilibiliAppParserHandler
2021-05-15 10:51:39.557 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.BiliBiliBangumiScheduleHandler
2021-05-15 10:51:39.558 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.BiliBiliBangumiScheduleHandler
2021-05-15 10:51:39.558 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.BotManagementHandler
2021-05-15 10:51:39.558 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.BotManagementHandler
2021-05-15 10:51:39.558 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.ChatRecorderHandler
2021-05-15 10:51:39.558 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.ChatRecorderHandler
2021-05-15 10:51:39.559 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.ChatReplyHandler
2021-05-15 10:51:39.559 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.ChatReplyHandler
2021-05-15 10:51:39.559 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.ExpressionSolverHandler
2021-05-15 10:51:39.560 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.ExpressionSolverHandler
2021-05-15 10:51:39.560 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.GenshinGachaSimulatorHandler
2021-05-15 10:51:39.560 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.GenshinGachaSimulatorHandler
2021-05-15 10:51:39.560 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.GroupWordCloudGeneratorHandler
2021-05-15 10:51:39.561 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.GroupWordCloudGeneratorHandler
2021-05-15 10:51:39.561 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.HeadHandler
2021-05-15 10:51:39.561 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.HeadHandler
2021-05-15 10:51:39.561 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.HotWordsExplainerHandler
2021-05-15 10:51:39.562 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.HotWordsExplainerHandler
2021-05-15 10:51:39.562 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.ImageAdderHandler
2021-05-15 10:51:39.562 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.ImageAdderHandler
2021-05-15 10:51:39.563 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.ImageSearchHandler
2021-05-15 10:51:39.563 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.ImageSearchHandler
2021-05-15 10:51:39.563 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.ImageSenderHandler
2021-05-15 10:51:39.563 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.ImageSenderHandler
2021-05-15 10:51:39.563 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.JLUCSWNoticeHandler
2021-05-15 10:51:39.563 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.JLUCSWNoticeHandler
2021-05-15 10:51:39.563 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.KeywordReplyHandler
2021-05-15 10:51:39.564 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.KeywordReplyHandler
2021-05-15 10:51:39.564 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.LatexGeneratorHandler
2021-05-15 10:51:39.664 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.LatexGeneratorHandler
2021-05-15 10:51:39.664 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.LeetcodeInfoHandler
2021-05-15 10:51:39.664 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.LeetcodeInfoHandler
2021-05-15 10:51:39.664 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.LoliconKeywordSearchHandler
2021-05-15 10:51:39.664 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.LoliconKeywordSearchHandler
2021-05-15 10:51:39.665 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.LOLItemRaidersHandler
2021-05-15 10:51:39.665 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.LOLItemRaidersHandler
2021-05-15 10:51:39.665 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.MarketingContentGeneratorHandler
2021-05-15 10:51:39.666 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.MarketingContentGeneratorHandler
2021-05-15 10:51:39.666 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.MessageMergeHandler
2021-05-15 10:51:39.667 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.MessageMergeHandler
2021-05-15 10:51:39.667 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.NetworkCompilerHandler
2021-05-15 10:51:39.667 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.NetworkCompilerHandler
2021-05-15 10:51:39.667 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.PDFSearchHandler
2021-05-15 10:51:39.667 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.PDFSearchHandler
2021-05-15 10:51:39.667 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.PeroDogHandler
2021-05-15 10:51:39.667 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.PeroDogHandler
2021-05-15 10:51:39.668 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.PhantomTankHandler
2021-05-15 10:51:39.668 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.PhantomTankHandler
2021-05-15 10:51:39.668 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.PoisonousChickenSoupHandler
2021-05-15 10:51:39.668 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.PoisonousChickenSoupHandler
2021-05-15 10:51:39.668 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.QrCodeGeneratorHandler
2021-05-15 10:51:39.668 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.QrCodeGeneratorHandler
2021-05-15 10:51:39.669 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.RepeaterHandler
2021-05-15 10:51:39.669 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.RepeaterHandler
2021-05-15 10:51:39.669 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.StatusPresenterHandler
2021-05-15 10:51:39.669 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.StatusPresenterHandler
2021-05-15 10:51:39.669 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.SteamGameInfoSearchHandler
2021-05-15 10:51:39.669 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.SteamGameInfoSearchHandler
2021-05-15 10:51:39.670 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.StylePictureGeneraterHandler
2021-05-15 10:51:39.670 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.StylePictureGeneraterHandler
2021-05-15 10:51:39.670 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.TodayInHistoryHandler
2021-05-15 10:51:39.670 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.TodayInHistoryHandler
2021-05-15 10:51:39.670 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.TrendingHandlers
2021-05-15 10:51:39.670 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.TrendingHandlers
2021-05-15 10:51:39.671 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.WhatToEatHandler
2021-05-15 10:51:39.676 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.WhatToEatHandler
2021-05-15 10:51:39.676 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.WolframAlphaHandler
2021-05-15 10:51:39.677 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.WolframAlphaHandler
2021-05-15 10:51:39.677 | DEBUG    | graia.saya:require:76 - require SAGIRIBOT.Handler.Handlers.__init__
2021-05-15 10:51:39.678 | INFO     | graia.saya:require:95 - module loading finished: SAGIRIBOT.Handler.Handlers.__init__
[2021-05-15 10:51:39,901][INFO]: initializing app...
[2021-05-15 10:51:39,910][INFO]: detecting remote's version...
2021-05-15 10:51:39.912 | INFO     | SAGIRIBOT.Core.AppCore:config_check:156 - checking config
2021-05-15 10:51:39.912 | INFO     | SAGIRIBOT.Core.AppCore:config_check:171 - check done
[2021-05-15 10:51:39,914][INFO]: detected remote's version: 1.9.8
[2021-05-15 10:51:39,916][INFO]: using pure websocket to receive event
[2021-05-15 10:51:39,916][INFO]: found websocket disabled, so it has been enabled.
[2021-05-15 10:51:39,918][INFO]: event receive method checked.
[2021-05-15 10:51:39,918][INFO]: this application's initialization has been completed.
[2021-05-15 10:51:39,918][INFO]: --- setting start ---
[2021-05-15 10:51:39,918][INFO]: broadcast using: <graia.broadcast.Broadcast object at 0x000002D410C5A730>
[2021-05-15 10:51:39,918][INFO]: enable log of chat: no
[2021-05-15 10:51:39,918][INFO]: debug: no
[2021-05-15 10:51:39,918][INFO]: version(remote): 1.9.8
[2021-05-15 10:51:39,918][INFO]: --- setting end ---
[2021-05-15 10:51:39,918][INFO]: application has been initialized, used 0.017s
[2021-05-15 10:51:39,919][INFO]: websocket daemon: websocket connection starting...
[2021-05-15 10:51:39,921][INFO]: websocket: connected
[2021-05-15 10:51:39,921][INFO]: websocket: ping task created
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:134 - 本次启动活动群组如下：
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
2021-05-15 10:51:41.860 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:136 - 群ID: 123456789     群名: xxxxxxx
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
| saucenaoApiKey | saucenao api key（自行获取） |
| webManagerApi | api是否启动（用于管理页面） |
| webManagerAutoBoot | 是否自动打开管理页面（webManagerApi为True时才起作用） |
| errorRetention | 错误日志记录周期 |
| commonRetention | 普通日志清空周期 |
| loliconApiKey | loliconapiKey，用于关键词涩图搜索功能 |
| loliconImageCache | 是否缓存loliconapi所获取到的图片 |
| wolframAlphaKey | wolframAlphaKey，用于科学计算api调用 |

## 使用文档

- [功能列表](docs/functions.md)
- [管理](docs/manage.md)
- [功能扩展](docs/function_extension.md)

因项目重构，原文档失效，新文档还在完善中🕊🕊🕊

## 注意
- 目前机器人尚未完善，仍有许多bug存在，若您在使用中发现了bug或有更好的建议，请提ISSUE

- 目前仅对sqlite数据库进行了适配，使用Mysql以及PostgreSQL产生的bug可能会很多并且会导致程序无法运行，若您需要稳定的运行请使用sqlite

- 支持的数据库类型请查看sqlalchemy文档

- 若您有好的解决方法可以PR，但请保证sqlite的兼容性

## TODO
- [x] 添加并完善日志记录功能
- [x] 支持Saya加载插件
- [x] 可视化管理页面
- [x] 支持发送语音
- [x] 完善文档
- [ ] 点歌功能
- [ ] 广告识别功能（自动禁言、撤回、移除）

## 鸣谢
- [mirai](https://github.com/mamoe/mirai) ，高效率 QQ 机器人框架 / High-performance bot framework for Tencent QQ

- [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，Mirai HTTP API (console) plugin

- [Graia Appliation](https://github.com/GraiaProject/Application) ，一个设计精巧, 协议实现完备的, 基于 mirai-api-http 的即时聊天软件自动化框架.

