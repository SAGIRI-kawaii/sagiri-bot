<div align="center">
    <img width="160" src="docs/sagiri.jpg" alt="logo"></br>
    <h1>SAGIRI-BOT</h1>
</div>
    
----

<div align="center">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg"/>
    <img src="https://img.shields.io/badge/sqlalchemy-1.4.11+-orange.svg"/>
    <h3>一个基于 Mirai 和 Graia-Ariadne 的QQ机器人</h3>
    <div>SAGIRI之名取自动漫《埃罗芒阿老师》中的角色 <a href="https://zh.moegirl.org.cn/%E5%92%8C%E6%B3%89%E7%BA%B1%E9%9B%BE">和泉纱雾(Izumi Sagiri)</a></div>
    <br>
    <div>若您在使用过程中发现了bug或有一些建议，欢迎提出ISSUE、PR或加入 <a href="https://jq.qq.com/?_wv=1027&k=9hfqo8AL">QQ交流群：788031679</a> </div>
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
- [丰富的功能](https://sagiri-kawaii.github.io/sagiri-bot/functions/handlers/)
- 可视化管理模块
- 基于loguru的日志系统
- 基于alembic的数据库版本管理功能

## 开始使用

### 使用前准备
不同于老版的SAGIRI-BOT，新版的SAGIRI-BOT使用了ORM框架，这意味着可以很方便的将项目适配各种不同的数据库

```diff
目前仅适配sqlite，使用mysql等产生的bug暂不在修复考虑范围内，但仍可提出ISSUE，在之后可能会修复
从v4迁移过来的用户请先进行数据库备份
```

- 配置数据库链接
    - sqlite: sqlite+aiosqlite:///filename.db
    - mysql: mysql+aiomysql://username:password@localhost:3306/dbname
    - 注意：请自行安装对应的异步库，如aiomysql、aiosqlite等
- 下载 [mirai-console](https://github.com/mamoe/mirai-console) 并配置 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，这些都可以在 [mirai](https://github.com/mamoe/mirai) 项目中找到
- 若上一条不会配置，请考虑使用 [mirai-console-loader](https://github.com/iTXTech/mirai-console-loader) 加载器进行配置
- 打开 `configdemo.yaml`，配置好个人信息，并将文件更名为 `config.yaml`，配置说明见[config文件参数说明](#configyaml)
- 打开 `alembic.ini` ，将 `sqlalchemy.url` 更换为自己的连接（不要使用异步引擎否则会报错）（如sqlite:///data.db）

### 如何启动

首先，启动 mirai-console，确保其正常运行且插件正常安装
在文件夹下执行 `python main.py` 即可
你应当见到类似如下格式的信息：
```text
2022-01-04 23:45:08.848 | INFO     | sagiri_bot.core.app_core:__init__:59 - Initializing
2022-01-04 23:45:08.916 | INFO     | sagiri_bot.core.app_core:__init__:84 - Initialize end
2022-01-04 23:45:08.921 | DEBUG    | graia.saya:require:111 - require sagiri_bot.handler.handlers.abbreviated_prediction
2022-01-04 23:45:08.939 | INFO     | graia.saya:require:134 - module loading finished: sagiri_bot.handler.handlers.abbreviated_prediction
...
                _           _            
     /\        (_)         | |           
    /  \   _ __ _  __ _  __| |_ __   ___ 
   / /\ \ | '__| |/ _` |/ _` | '_ \ / _ \
  / ____ \| |  | | (_| | (_| | | | |  __/
 /_/    \_\_|  |_|\__,_|\__,_|_| |_|\___|
Ariadne version: 0.4.9
Broadcast version: 0.14.5
Scheduler version: 0.0.6
Saya version: 0.0.13
2022-01-04 23:45:11.200 | INFO     | graia.ariadne.app:launch:1287 - Launching app...
2022-01-04 23:45:11.200 | DEBUG    | graia.ariadne.app:daemon:1208 - Ariadne daemon started.
2022-01-04 23:45:11.246 | INFO     | graia.ariadne.adapter:fetch_cycle:378 - websocket: connected
2022-01-04 23:45:13.256 | INFO     | graia.ariadne.app:launch:1295 - Remote version: 2.4.0
2022-01-04 23:45:13.256 | INFO     | graia.ariadne.app:launch:1298 - Application launched with 2.1s
2022-01-04 23:45:13.256 | INFO     | sagiri_bot.core.app_core:config_check:206 - Start checking configuration
2022-01-04 23:45:13.257 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - bot_qq - 123
2022-01-04 23:45:13.257 | SUCCESS  | sagiri_bot.core.app_core:config_check:215 - data_related:
2022-01-04 23:45:13.257 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     lolicon_image_cache - true
2022-01-04 23:45:13.257 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     lolicon_data_cache - true
2022-01-04 23:45:13.257 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     network_data_cache - true
2022-01-04 23:45:13.258 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     automatic_update - false
2022-01-04 23:45:13.258 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     data_retention - true
2022-01-04 23:45:13.258 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - db_link - sqlite+aiosqlite:///data.db
2022-01-04 23:45:13.258 | SUCCESS  | sagiri_bot.core.app_core:config_check:215 - functions:
2022-01-04 23:45:13.258 | SUCCESS  | sagiri_bot.core.app_core:dict_check:196 -     tencent:
2022-01-04 23:45:13.259 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -         secret_id - xxx
2022-01-04 23:45:13.259 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -         secret_key - xxx
2022-01-04 23:45:13.259 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     saucenao_api_key - xxx
2022-01-04 23:45:13.259 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     loliconApiKey - xxx
2022-01-04 23:45:13.259 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     wolfram_alpha_key - xxx
2022-01-04 23:45:13.259 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     shadiao_app_name - xxx
2022-01-04 23:45:13.260 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - host_qq - 123
2022-01-04 23:45:13.260 | SUCCESS  | sagiri_bot.core.app_core:config_check:215 - image_path:
2022-01-04 23:45:13.260 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     setu - M:\Pixiv\pxer_new\
2022-01-04 23:45:13.260 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     setu18 - M:\Pixiv\pxer18_new\
2022-01-04 23:45:13.260 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     real - M:\Pixiv\reality\
2022-01-04 23:45:13.261 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     real_highq - M:\Pixiv\reality\highq\
2022-01-04 23:45:13.261 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     wallpaper - M:\Pixiv\bizhi\highq\
2022-01-04 23:45:13.261 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     sketch - M:\线稿\
2022-01-04 23:45:13.261 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     cg - M:\二次元\CG\画像\ev\
2022-01-04 23:45:13.262 | SUCCESS  | sagiri_bot.core.app_core:config_check:215 - log_related:
2022-01-04 23:45:13.262 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     error_retention - 14
2022-01-04 23:45:13.262 | SUCCESS  | sagiri_bot.core.app_core:dict_check:201 -     common_retention - 7
2022-01-04 23:45:13.262 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - mirai_host - http://localhost:23456
2022-01-04 23:45:13.263 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - proxy - http://localhost:12345
2022-01-04 23:45:13.263 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - verify_key - 1234567890
2022-01-04 23:45:13.263 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - web_manager_api - True
2022-01-04 23:45:13.263 | SUCCESS  | sagiri_bot.core.app_core:config_check:220 - web_manager_auto_boot - True
2022-01-04 23:45:13.263 | INFO     | sagiri_bot.core.app_core:config_check:221 - Configuration check completed
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:171 - 本次启动活动群组如下：
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
```
现在，来试一试你的机器人吧！

### 参数说明

#### config.yaml
用于存储机器人的各种配置，可随时进行更改
注意：所有路径的结尾都应该有斜杠，如："/bot/setuPath/" 或 "\bot\setuPath\" 等

| 参数名                   | 说明                                              |
|-----------------------|-------------------------------------------------|
| bot_qq                | 机器人的QQ号                                         |
| host_qq               | 主人的QQ号，默认权限等级4                                  |
| verify_key            | mirai-api-http 的 verify_key，格式为 `!!str authKey` |
| mirai_host            | 主机ip + mirai-api-http 的 port，一般在本地不用更改          |
| db_link               | 数据库链接，可参看 [使用前准备](#使用前准备)                       |
| web_manager_api       | api是否启动（用于管理页面）\[暂未实现]                          |
| web_manager_auto_boot | 是否自动打开管理页面（webManagerApi为True时才起作用）\[暂未实现]      |
| image_path            | 图库路径，可自行添加图库，已给出六个自带图库                          |
| setu                  | 二次元图片存储路径（绝对路径）                                 |
| setu18                | 不对劲二次元图片存储路径（绝对路径）                              |
| real                  | 三次元图片存储路径（绝对路径）                                 |
| real_highq            | 高质量三次元图片存储路径（绝对路径）                              |
| wallpaper             | 壁纸图片存储路径（绝对路径）                                  |
| sketch                | 线稿图片存储路径（绝对路径）                                  |
| functions             | 功能相关                                            |
| tencent-secret_id     | 腾讯云secret_id（自行申请）                              |
| tencent-secret_key    | 腾讯云secret_key（自行申请）                             |
| shadiao_app_name      | shadiaoApp 应用名（自行申请）                            |
| saucenao_api_key      | saucenao api key（自行获取）                          |
| wolfram_alpha_key     | wolframAlphaKey，用于科学计算api调用                     |
| github-user_name      | GitHub 用户名，用于订阅 Github 仓库变动                     |
| github-token          | GitHub 用户 Token ，用于订阅 Github 仓库变动               |
| log_related           | 日志相关                                            |
| error_retention       | 错误日志记录周期                                        |
| common_retention      | 普通日志清空周期                                        |
| lolicon_image_cache   | 是否缓存lolicon api所获取到的图片                          |
| lolicon_data_cache    | 是否缓存lolicon api所获取到的json数据                      |
| network_data_cache    | 自动保存各api的数据（暂未实现）                               |
| automatic_update      | 自动更新（暂未实现）                                      |
| data_retention        | 退群后的数据处理                                        |
| database_related      | 数据库相关（若不了解请不要修改这一部分，用于自定义engine参数）              |

## 使用文档

[文档链接](https://sagiri-kawaii.github.io/sagiri-bot/)

## 注意
- 目前机器人尚未完善，仍有许多bug存在，若您在使用中发现了bug或有更好的建议，请提ISSUE

- 目前仅对 sqlite 数据库进行了适配，使用 Mysql 以及 PostgreSQL 产生的bug可能会很多并且会导致程序无法运行，若您需要稳定的运行请使用sqlite

- 支持的数据库类型请查看sqlalchemy文档

- 若您有好的解决方法可以PR，但请保证sqlite的兼容性

## 鸣谢
- [mirai](https://github.com/mamoe/mirai) ，高效率 QQ 机器人框架 / High-performance bot framework for Tencent QQ

- [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，Mirai HTTP API (console) plugin

- [Graia Ariadne（目前使用）](https://github.com/GraiaProject/Ariadne) ，一个优雅且完备的 Python QQ 自动化框架。基于 Mirai API HTTP v2。

- [Graia Appliation（老版使用）](https://github.com/GraiaProject/Application) ，一个设计精巧, 协议实现完备的, 基于 mirai-api-http 的即时聊天软件自动化框架.

- 特别感谢 [JetBrains](https://www.jetbrains.com/?from=sagiri-bot) 为开源项目提供免费的 [PyCharm](https://www.jetbrains.com/pycharm/?from=sagiri-bot) 等 IDE 的授权  

[<img src=".github/jetbrains-variant-3.png" width="200"/>](https://www.jetbrains.com/?from=sagiri-bot)