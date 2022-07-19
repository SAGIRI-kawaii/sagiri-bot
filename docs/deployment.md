# 项目部署

## 安装java & python

这部分若您不会请通过搜索引擎自行完成

请注意其中 `python版本 >= 3.8`

## 安装anaconda（推荐）

## 安装[mirai](https://github.com/mamoe/mirai)

### 使用 [mcl-installer](https://github.com/iTXTech/mcl-installer) 进行安装（推荐）
- 从 [mcl-installer release](https://github.com/iTXTech/mcl-installer/releases/latest) 下载适合 **你电脑架构** 的版本

- 下载完成后，打开终端，**前往下载文件所在文件夹**，输入 `./mcl-installer`，你应当见到如下输出：

```text
iTXTech MCL Installer 1.0.3 [OS: windows]
Licensed under GNU AGPLv3.
https://github.com/iTXTech/mcl-installer

iTXTech MCL and Java will be downloaded to "F:\PythonProjects\mah-pure-inst"

Checking existing Java installation.
...
Would you like to install Java? (Y/N, default: Y)
```

一路回车即可（也可以按照自己情况进行修改）

- 随后运行 `./mcl`，你应当见到如下输出：

```text
[INFO] Verifying "net.mamoe:mirai-console" v
[ERROR] "net.mamoe:mirai-console" is corrupted.
Downloading ......
xxxx-xx-xx xx:xx:xx I/main: Starting mirai-console...
......
xxxx-xx-xx xx:xx:xx I/main: mirai-console started successfully.

>
```

- 此时输入 `/autoLogin add` <你的QQ号> <你的QQ密码> 并回车，应该会显示 已成功添加 '<你的QQ号>'

- 退出 `mirai-console`

### 使用 [mirai-console-loader(mcl)](https://github.com/iTXTech/mirai-console-loader) 进行安装

- 打开mcl的 [release](https://github.com/iTXTech/mirai-console-loader/releases) 页面，点击 `mcl-x.x.x.zip` 下载最新版本
- `Windows系统` 在下载后解压运行 `mcl.cmd`
- `Linux系统` 在下载后解压运行 `mcl`

### 自行安装

- 这就靠你自己咯（
- mirai项目地址在这个页面有哦~自己找找吧~

## 安装 [mirai-api-http-v2](https://github.com/project-mirai/mirai-api-http)

### 通过 [mirai-console-loader(mcl)](https://github.com/iTXTech/mirai-console-loader) 进行安装（推荐）

- 按照 `mcl` 的 `README`，运行 `./mcl --update-package net.mamoe:mirai-api-http --channel stable-v2 --type plugin`
- 启动 `mcl` 完成自动更新和启动

### 自行安装

- 自行下载jar包并塞入 `plugins` 文件夹

## 配置 [mirai-api-http-v2](https://github.com/project-mirai/mirai-api-http)

### 使用 [mirai-console-loader(mcl)](https://github.com/iTXTech/mirai-console-loader) 配置

- 打开 `MCL/config/net.mamoe.mirai-api-http/setting.yml`

内容如下：
```yaml
adapters:
  - http
  - ws
debug: false
enableVerify: true
verifyKey: ServiceVerifyKey # 你可以自己设定, 这里作为示范
singleMode: false
cacheSize: 4096 # 可选, 缓存大小, 默认4096. 缓存过小会导致引用回复与撤回消息失败
adapterSettings:
  ## 详情看 http adapter 使用说明 配置
  http:
    host: localhost
    port: 8080 # 端口
    cors: [*]

  ## 详情看 websocket adapter 使用说明 配置
  ws:
    host: localhost
    port: 8080 # 端口
    reservedSyncId: -1 # 确保为 -1, 否则 WebsocketAdapter(Experimental) 没法正常工作.
```

### 自行配置

请自行查看 [mirai-api-http](https://github.com/project-mirai/mirai-api-http)

## 登录QQ

执行 `./mcl` 启动 `mirai-console`

如果直接显示 `Event: BotOnlineEvent(bot=Bot(<你的QQ号>))`，并有收到新消息，那么恭喜你，你已经完成了 `mirai` 方面的配置了

若显示如下输出或出现有如下内容的弹窗：

```text
需要滑动验证码，完成后请输入ticket
url:http://xxx.xxx.xxx
```

- 有弹窗，并且使用的是 `Android` 系统手机（或使用电脑模拟器）
    - 点击 `Open with TxCaptchaHelper`，下载 [TxCaptchaHelper](https://maupdate.rainchan.win/txcaptcha.apk) 并安装
    - 输入弹窗中的4位请求码并完成滑动验证，随后在电脑端点击确定

- 没弹窗（如 Linux NoGUI 用户）或者使用的 `IOS` 系统手机/其他不能运行 `apk` 程序系统的手机
    - 在电脑上打开浏览器，输入程序提供的url，应当会出现滑动认证的画面，此时先不要进行认证
    - 单击 `F12` 键，会出现一个 `DevTool`，找到上方选项卡，点击 `Network` 选项，再点击下方的 `Fetch/XHR` 选项
    - 完成滑动验证，此时在 `DevTool` 界面中应会出现新的请求，找到其中名为 `cap_union_new_verify` 选项卡，点击其中的 `Preview` 选项卡，在其中找到 `ticket` 的值填入 `mcl` 并回车
    - gif演示：![浏览器获取ticket演示](https://sagiri-kawaii.github.io/sagiri-bot/assets/txcaptcha.gif)

## 配置python环境

`pip install -r requirements.txt`

## 配置config

- 打开 `configdemo.yaml`
- 按文件中注释更改
- 将文件更名为 `config.yaml`

## 配置 `alembic`

- 运行一次bot ( `python main.py` )，bot应会自动退出
- 在目录下寻找 `alembic.ini` 文件并打开
- 将其中 `sqlalchemy.url` 项更换为自己的连接（不需注明引擎否则会报错）（如sqlite:///data.db）

## 启动机器人

1. 启动 `mcl`
2. 进入bot目录下执行 `python main.py`

你应当见到如下界面：
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
2022-01-04 23:45:13.570 | INFO     | sagiri_bot.handler.required_module.saya_manager.utils:saya_init:51 - converting saya module: sagiri_bot.handler.handlers.abbreviated_prediction
2022-01-04 23:45:13.571 | WARNING  | sagiri_bot.handler.required_module.saya_manager.utils:saya_init:61 - 插件AbbreviatedPrediction未使用inline_dispatchers！默认notice为False！
2022-01-04 23:45:13.575 | INFO     | sagiri_bot.handler.required_module.saya_manager.utils:saya_init:51 - converting saya module: sagiri_bot.handler.handlers.abstract_message_transform
2022-01-04 23:45:13.578 | INFO     | sagiri_bot.handler.required_module.saya_manager.utils:saya_init:51 - converting saya module: sagiri_bot.handler.handlers.avatar_fun
2022-01-04 23:45:13.578 | WARNING  | sagiri_bot.handler.required_module.saya_manager.utils:saya_init:61 - 插件AvatarFunPic未使用inline_dispatchers！默认notice为False！
2022-01-04 23:45:13.580 | INFO     | sagiri_bot.handler.required_module.saya_manager.utils:saya_init:51 - converting saya module: sagiri_bot.handler.handlers.bangumi_info_searcher
2022-01-04 23:45:13.580 | WARNING  | sagiri_bot.handler.required_module.saya_manager.utils:saya_init:61 - 插件BangumiInfoSearcher未使用inline_dispatchers！默认notice为False！
...
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

其中 `...` 为省略的类似内容

现在，来试一试你的机器人吧！