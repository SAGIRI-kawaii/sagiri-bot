[TOC]


# SAGIRI-BOT

基于 Mirai 和 Graia 的船新版本，~~是兄弟就来砍我~~

New version of sagiri-bot based on Mirai and Graia

## 使用文档

文档缓慢更新中（老鸽子了）

文档地址: http://doc.sagiri-web.com/web/#/p/c79d523043f6ec05c1ac1416885477c7

## 开始使用

### 使用前准备

- 使用 `pip install -r requirements` 命令安装所需库
- 执行 `dbInit.sql` 文件，这将帮助你建立一个适合 SAGIRI-BOT 的数据库
- 下载 [mirai-console](https://github.com/mamoe/mirai-console) 并配置 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，这些都可以在 [mirai](https://github.com/mamoe/mirai) 项目中找到
- 打开 `configdemo.json`，配置好个人信息，并将文件更名为 `config.json`，配置说明见[config文件参数说明](#config)
- ~~最重要的当然是准备好各种图片~~

### 如何启动

在文件夹下执行 `python sagiri-bot.py` 即可
你应当见到类似如下格式的信息：
```angular2
[2020-12-01 11:42:02,059][INFO]: initializing app...
[2020-12-01 11:42:02,069][INFO]: detecting remote's version...
[2020-12-01 11:42:02,073][INFO]: detected remote's version: 1.7.3
[2020-12-01 11:42:02,075][INFO]: using pure websocket to receive event
[2020-12-01 11:42:02,075][INFO]: found websocket disabled, so it has been enabled.
Bot init start
[2020-12-01 11:42:02,077][INFO]: event receive method checked.
[2020-12-01 11:42:02,077][INFO]: this application's initialization has been completed.
[2020-12-01 11:42:02,077][INFO]: --- setting start ---
[2020-12-01 11:42:02,077][INFO]: broadcast using: <graia.broadcast.Broadcast object at 0x00000233C18D8688>
[2020-12-01 11:42:02,078][INFO]: enable log of chat: yes
[2020-12-01 11:42:02,078][INFO]: debug: no
[2020-12-01 11:42:02,078][INFO]: version(remote): 1.7.3
[2020-12-01 11:42:02,078][INFO]: --- setting end ---
[2020-12-01 11:42:02,078][INFO]: application has been initialized, used 0.019s
[2020-12-01 11:42:02,079][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,082][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,083][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,085][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,086][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,087][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,089][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,090][DEBUG]: caching sha2: succeeded by fast path.
[123564623, 12343143214, 45346146, 6135464, 13461463143, 123413241234, 652466542, 8679675867, 45142316431, 123442341]
123564623 : xxxxxxxx
12343143214 : xxxxxxxx
45346146 : xxxxxxxx
6135464 : xxxxxxxx
13461463143 : xxxxxxxx
123413241234 : xxxxxxxx
652466542 : xxxxxxxx
8679675867 : xxxxxxxx
45142316431 : xxxxxxxx
123442341 : xxxxxxxx
{123564623, 12343143214, 45346146, 6135464, 13461463143, 123413241234, 652466542, 08679675867, 45142316431, 123442341}
Bot init end
[2020-12-01 11:42:02,092][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,093][DEBUG]: caching sha2: succeeded by fast path.
[2020-12-01 11:42:02,094][DEBUG]: caching sha2: succeeded by fast path.
```
其中各种数字为此账号所加入的所有群组的群号，冒号后面xxxxxxxx的为群号对应群名
现在，来试一试你的机器人吧！

### 参数说明

#### config.json<span id="config"></span>
用于存储机器人的各种配置，可随时进行更改

|  参数名   | 说明  |
|  ----  | ----  |
| BotQQ  | 机器人的QQ号 |
| HostQQ  | 主人的QQ号，也可理解为超级管理员的QQ号 |
| authKey | mirai-api-http 的 authKey |
| miraiHost | 主机ip + mirai-api-http 的 port，一般在本地不用更改 |
| dbHost | 数据库地址 |
| dbName | 数据库名 |
| dbUser | 数据库账号用户名 |
| dbPass | 数据库账号密码 |
| setuPath | 正常二次元图片存储路径（绝对路径） |
| setu18Path | 不对劲二次元图片存储路径（绝对路径） |
| realPath | 三次元图片存储路径（绝对路径） |
| realHighqPath | 高质量三次元图片存储路径（绝对路径） |
| searchPath | 搜图功能的图片缓存路径（绝对路径） |
| yellowJudgePath | 鉴黄功能的图片缓存路径（绝对路径） |
| clockWallpaperPreviewPath | 钟表功能表盘预览图片存储路径（绝对路径） |
| clockWallpaperSavedPath | 钟表功能表盘图片存储路径（有时间的）（绝对路径） |
| tributePath | 上贡图片存储路径（暂未从旧版本迁移过来）（绝对路径） |
| wallpaperPath | 壁纸图片存储路径（绝对路径） |
| imgSavePath | 番剧查询功能图片缓存地址（绝对路径） |
| listenImagePath | 图片监听，私发存图存储路径（绝对路径） |
| txAppId | 腾讯AI开放平台AppId（自行申请） |
| txAppKey | 腾讯AI开放平台AppKey（自行申请） |
| shadiaoAppName | shadiaoApp 应用名（自行申请） |

#### response_set.json
用于存储各种功能触发的关键词，需要在机器人启动前进行更改，机器人运行时更改无效（将在下次启动时生效）

|  参数名   | 说明  |
|  ----  | ----  |
| setu  | 二次元图片功能触发关键词（可添加图片，按照\[mirai:image:{ImageMD5}.mirai\]的格式添加即可，可使用 `message.asSerializationString()` 函数查看） |
| real | 三次元图片功能触发关键词（可添加图片，按照\[mirai:image:{ImageMD5}.mirai\]的格式添加即可，可使用 `message.asSerializationString()` 函数查看） |
| bizhi | 壁纸图片功能触发关键词（可添加图片，按照\[mirai:image:{ImageMD5}.mirai\]的格式添加即可，可使用 `message.asSerializationString()` 函数查看） |
| realHighq | 高质量三次元图片功能触发关键词（可添加图片，按照\[mirai:image:{ImageMD5}.mirai\]的格式添加即可，可使用 `message.asSerializationString()` 函数查看） |


## 鸽子宣言
剩下的过两天再写.jpg