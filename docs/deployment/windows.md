# Windows 部署

!!! danger "使用前注意"
    
    本教程需要：
    
    - 基础文件操作能力
    
    - 基础终端使用能力
    
    - 基础搜索引擎使用能力
    
    - 中文阅读理解能力
    
    - 一个可以正常运转的脑子
    
    没有的话建议快跑

!!! danger "一个建议"
    
    极度不建议没有任何计算机基础的人安装或使用 SAGIRI-BOT!
    
    除非你懂得如何阅读文档、虚心提问并可以正常使用搜索引擎

!!! note "关于部署出现问题"

    当部署出现问题时，请检查是否按文档顺序进行，如出现问题可前往 [FAQ](/FAQ/) 寻找，如果没有找到原因可以前往 [SAGIRI BOT官方交流群](https://jq.qq.com/?_wv=1027&k=9hfqo8AL) 询问或在 github 提出 ISSUE

!!! note "其他选择"

    对于 `mirai` 的部署部分，如果有感觉写的不清楚的地方，可以查看官方/社区的部署教程，效果是相同的
    
    - [官方文档 - Mirai API HTTP 安装](https://graia.cn/ariadne/appendix/mah-install/)
    
    - [社区文档 - Mirai 的安装与配置](https://graiax.cn/before/install_mirai.html)
    
## 安装 Mirai

本章分为使用 [mirai-console-loader](https://github.com/iTXTech/mirai-console-loader) 安装（推荐）和使用 [mcl-installer](https://github.com/iTXTech/mcl-installer) 安装两部分

我们推荐使用 [mirai-console-loader](https://github.com/iTXTech/mirai-console-loader) 进行安装

我们不推荐直接下载 [Mirai](https://github.com/mamoe/mirai) 使用，如果你确定自己会用，请自行部署

### 使用 [mirai-console-loader](https://github.com/iTXTech/mirai-console-loader) 安装

#### 安装 Java

关于 Java 的安装，可以查看社区文档 [安装 Java](https://graiax.cn/before/install_mirai.html#%E5%AE%89%E8%A3%85-java)（我懒得写）

#### 安装 [mirai-console-loader](https://github.com/iTXTech/mirai-console-loader)
- 打开mcl的 [release](https://github.com/iTXTech/mirai-console-loader/releases) 页面，点击 `mcl-x.x.x.zip` 下载最新版本
- 下载后解压并双击运行 `mcl.cmd`，如果你的电脑没有打开文件后缀显示，则双击那个图标里有齿轮的 `mcl`
- 等待运行完成

### 使用 [mcl-installer](https://github.com/iTXTech/mcl-installer) 安装
- 从 [mcl-installer release](https://github.com/iTXTech/mcl-installer/releases/latest) 下载 `mcl-installer-x.x.x-windows-amd64.exe` 并运行
- 下载完成后，双击 `mcl-installer-x.x.x-windows-amd64.exe`，你应当见到如下输出：

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

- 随后运行 `./mcl.cmd`，你应当见到如下输出：

```text
[INFO] Verifying "net.mamoe:mirai-console" v
[ERROR] "net.mamoe:mirai-console" is corrupted.
Downloading ......
xxxx-xx-xx xx:xx:xx I/main: Starting mirai-console...
......
xxxx-xx-xx xx:xx:xx I/main: mirai-console started successfully.

>
```

- 点击右上角 `X` 退出 `mirai-console`

## 安装 [mirai-api-http-v2](https://github.com/project-mirai/mirai-api-http)

首先，我们进入 `cmd`，并进入 `mirai-console-loader` 的文件夹下，如果你在安装 Mirai 时使用的是使用的是 `mcl-installer`，则进入 `mcl-installer` 下面的 `mcl` 文件夹

如果你不会进入，在文件资源管理器中打开对应文件夹，点击路径栏，输入 `cmd` 并回车

- 按照 `mirai-api-http` 的 `README`，在 `cmd` 中粘贴并运行 `.\mcl --update-package net.mamoe:mirai-api-http --channel stable-v2 --type plugin`
- 切换 `mirai-console-loader` 的 `repo`，运行 `.\mcl --mrm-use forum`（当出现网络报错时执行）
- 启动 `mcl` 完成自动更新和启动

### 配置 mirai-api-http-v2

- 打开 `mcl/config/net.mamoe.mirai-api-http/setting.yml`，将下面的内容复制覆盖粘贴到文件中
- 若无此文件请检查 `mcl` 是否被成功添加并且添加后启动过一次 `mcl`，若没有请完成前文所述步骤再进行此步骤
```yaml
adapters:
  - http
  - ws
debug: false
enableVerify: true
verifyKey: 1234567890 # 你可以自己设定, 这里作为示范, 请保持和 config.yaml 中 verify_key 项一致
singleMode: false
cacheSize: 4096 # 可选, 缓存大小, 默认4096. 缓存过小会导致引用回复与撤回消息失败
adapterSettings:
  ## 详情看 http adapter 使用说明 配置
  http:
    host: localhost
    port: 23456 # 端口
    cors: [*]

  ## 详情看 websocket adapter 使用说明 配置
  ws:
    host: localhost
    port: 23456 # 端口
    reservedSyncId: -1 # 确保为 -1, 否则 WebsocketAdapter(Experimental) 没法正常工作.
```

!!! warning "安装注意"
    
    当启动后出现如下方的消息才算安装并启动成功
    
    ```text
    2022-04-30 12:20:17 I/Mirai HTTP API: ********************************************************
    2022-04-30 12:20:17 I/http adapter: >>> [http adapter] is listening at http://localhost:23456
    2022-04-30 12:20:17 I/ws adapter: >>> [ws adapter] is listening at ws://localhost:23456
    2022-04-30 12:20:17 I/Mirai HTTP API: Http api server is running with verifyKey: 1234567890
    2022-04-30 12:20:17 I/Mirai HTTP API: adaptors: [http,ws]
    2022-04-30 12:20:17 I/Mirai HTTP API: ********************************************************
    ```

## 配置自动登录

!!! warning "注意"

    为防止因填入不当数据导致无法启动 mirai-console-loader (MCL) 的问题，**建议在部署时通过 mirai-console-loader (MCL) 内建的 `autoLogin` 指令配置自动登录**，而非直接修改 Console 配置文件

### 使用 /autoLogin 配置自动登录（推荐）

在 mirai-console-loader (MCL) 启动完成后，输入 `/autoLogin add <你的QQ号> <你的QQ密码>` 并回车，应该会显示 `已成功添加 '<你的QQ号>'`

### 修改 Console 配置文件实现自动登录（不推荐）

!!! warning "仅可在 mirai-console-loader (MCL) 已关闭的情况下更改配置文件"

使用合适的编辑器打开位于 mirai-console-loader (MCL) 安装目录下的 `config/Console/AutoLogin.yml` 文件，应类似于如下内容：

```yaml
accounts: 
    account: 123456    # 需要自动登录的 QQ 号
    password:     # 这行不填！！！这行不填！！！这行不填！！！
      kind: PLAIN    #       # 密码种类, 可选 PLAIN 或 MD5，看不懂保持默认即可
      value: pwd    # QQ 号对应的登录密码，PLAIN 时为密码文本, MD5 时为 16 进制
    configuration: 
      protocol: ANDROID_PHONE    # 登录协议，看不懂保持默认即可，可选 "ANDROID_PHONE" / "ANDROID_PAD" / "ANDROID_WATCH" /"MAC" / "IPAD"
```

修改 `account` `kind` `value` `protocol` 的值并保存即可完成自动登录的配置

??? note "如何实现手机和 mirai 同时在线？"

    可通过更改登录协议实现，操作如下：

    在已配置自动登录后，输入 `/autoLogin setConfig <你的QQ号> protocol IPAD`

    指令中的 `IPAD` 可更换为其他登录协议，如 `ANDROID_PAD` `ANDROID_WATCH` 等，推荐使用 `IPAD` 登录协议以防止出现部分功能无法使用的情况

    注意：更改协议后需要重启 `mcl` 才可生效

    > 什么？你想手机平板手表电脑和 mirai 同时在线？

    > 我的建议是，为什么不问问万能的神奇海螺呢？

## 登录 QQ

执行 `.\mcl` 启动 `mirai-console`

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
    - gif演示：![浏览器获取ticket演示](../assets/txcaptcha.gif)

若显示需要手机验证码登录按提示操作即可

## 安装 python

!!! danger "安装前请注意"

    如果你要使用使用到深度学习库的项目，强烈推荐使用 Anaconda/Miniconda 安装 Python
    
    如果你了解这些库的配置等，可自行决定

### 使用 Anaconda/Miniconda

- 如果你的机器存储空间足够大，则打开 [Anaconda 官网下载地址](https://www.anaconda.com/download/)，否则请打开 [Miniconda 官网下载地址](https://docs.conda.io/en/latest/miniconda.html)，下载安装包并安装
- 配置环境变量
    - 打开开始栏，输入 `编辑系统环境变量` 并搜索，进入环境变量编辑界面
    - 找到用户变量中 `PATH` 项并双击
    - 添加 `path_to_anaconda\Scripts`，例如我的Anaconda安装路径为 `S:\Anaconda3`，则要添加的项为 `S:\Anaconda3\Scripts`
    - 使用 win + r 组合键，打开运行窗口，输入 `cmd` 并回车，打开命令提示符
    - 输入 `conda --version`，若输出如 `conda 4.8.4` 的消息就证明配置成功
- 创建虚拟环境（可选但推荐）
    - 使用 win + r 组合键，打开运行窗口，输入 `cmd` 并回车，打开命令提示符
    - 输入 `conda create -n your_env_name python=3.10`，其中 `your_env_name` 为你要创建的环境名，可自定义，python版本 >= 3.10 即可，可自行安装其他版本
    - 等待程序询问是否安装，直接回车即可
    - 安装完毕后输入 `conda activate your_env_name` 即可激活虚拟环境

### 自行安装

搜索引擎会告诉你一切，搜索关键词：`Windows python3.10安装`，注意，安装的python版本必须大于等于3.10！

## 下载 SAGIRI-BOT

### 使用 git

- 打开终端，进入你想要下载的目标文件夹
- 输入 `git clone https://github.com/SAGIRI-kawaii/sagiri-bot.git`
- 等待下载完成即可
- 什么？你问我太慢怎么办？我的建议是，找一台可以快速链接 `github` 的机器下载再传过来
- 或者你可以使用代理站：`git clone https://ghproxy.com/github.com/SAGIRI-kawaii/sagiri-bot.git`

### 直接下载

- 打开 [SAGIRI-BOT 项目地址](https://github.com/SAGIRI-kawaii/sagiri-bot) ，点击绿色的 `Code` 按钮，并点击下面的 `Download ZIP`
- 下载完成后解压即可
- 什么？你问我太慢怎么办？我的建议是，找一台可以快速链接 `github` 的机器下载再传过来

!!! danger "***真的非常不建议***直接从 GitHub 下载仓库的 zip 或 tar 文件"

    大部分情况下，直接使用 zip 或 tar 文件进行安装无法通过 `git pull` 进行更新，即使用该方法，可能无法正常更新且可能有稳定性问题

    <del>如果是因为直接下的 zip 或 tar 文件而且一直没更新导致的问题，就不要跑来群里或者发 issue 问了</del>


## 配置 python 虚拟环境并安装依赖

!!! question "为什么要配置python虚拟环境？"

    防止出现依赖混乱或冲突等问题，常用的虚拟环境有 `conda` `venv` `poetry` 等

    <del>当然你也可以不配置，但是如果你不配置而且服务器上还有其他的一些python项目，那么你的程序可能会出现一些问题</del>

!!! warning "此处将默认你已经安装了 `poetry`"

    不会安装 `poetry` ？

    在 PowerShell 执行 `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -` 即可安装 `poetry`

    随后在 `.bashrc` 或 `.zshrc` 中添加脚本打印的 `export` 以便在终端中使用 `poetry` 命令

    实在不会，你就 `pip install poetry`

### 使用 Anaconda/Miniconda

- 若你在安装python时使用的是安装 Anaconda/Miniconda 的方法并且 `自带python版本>=3.10` 或已经配置好虚拟环境可观看此项
- 使用 win + r 组合键，打开运行窗口，输入 `cmd` 并回车，打开命令提示符
- 输入 `conda activate your_env_name` 进入虚拟环境（Anaconda自带版本 >= 3.10可忽略此步骤，但推荐使用虚拟环境以防止出现依赖混乱冲突的情况，若你还没有创建虚拟环境并且自带python版本不符合条件，请查看上方创建虚拟环境）
- 激活成功后进入bot所在目录，因为我们使用 `conda` 创建虚拟环境，所以要先关闭 `poetry` 的虚拟环境创建，在终端执行 `poetry config virtualenvs.create false`
- 在终端输入 `poetry env info`，当其中的的 `Valid` 项为 `True` 时，就代表 `poetry` 已经可以在 `conda` 的虚拟环境中使用了
- 执行 `poetry install`，等待安装完成

### 使用 poetry

- 使用 win + r 组合键，打开运行窗口，输入 `cmd` 并回车，打开命令提示符
- 进入 bot 所在目录，运行 `poetry install` 即可

??? note "`Resolving dependencies...` 部分耗时过长？"

    首先检查一下是否误删了 `poetry.lock` 文件

    如果误删了，可以使用 `git checkout poetry.lock` 恢复

    如果没有误删，那么不用慌张！<del>这是技术性调整</del>

    可能是因为你的网络不稳定，或者你的网络环境不符合要求，导致 `poetry install` 失败，请尝试使用 `pip` 安装依赖

    > 大概需要多久安装成功呢？

    > 截至这个区块编写完成，已知的最长用时是 20 分钟。

## 配置 config

- 打开 `/config/config_demo.yaml`
- 按文件中注释更改
- 将文件更名为 `/config/config.yaml`

???+ note "不知道怎么改数据库链接？"

    **如果没有特殊需求，或者你不知道这是什么意思，保持不变即可。**

    如需要指定使用的数据库或使用 MySQL 等，则需要更改至相应链接，格式如下：

    - SQLite

        > `sqlite+aiosqlite:///data.db`

        > 使用该链接将使用 SAGIRI-BOT 部署目录下的 `data.db`

    - MySQL

        > `mysql+aiomysql://username:password@ip:port/database`

        > 使用该链接将以 `username` 为用户名，`password` 为密码连接至位于 `ip:port` 的 `database` 数据库

    - 其他数据库

        > 不知道捏，自己探索吧

        > 可查阅 SQLAlchemy 使用文档填写合适的链接

    **如果你看不懂上述文本的话保持不变即可。**

## 配置 `alembic`

- 首先启动 `mcl`
- 运行一次bot ( `python main.py` )，bot应会自动退出
- 在目录下寻找 `alembic.ini` 文件并打开
- 将其中 `sqlalchemy.url` 项更换为自己的连接（不需注明引擎否则会报错）（如 `sqlite:///data.db`）

???+ note "不知道什么是引擎？"

    <big>**如果你在上一步保持不变，这一步填写 `sqlite:///data.db` 即可**</big>

    - SQLite

        > 假设你在上一步配置的链接为 `sqlite+aiosqlite:///data.db`

        > 则你在这一步配置的链接应为 `sqlite:///data.db`

    - MySQL

        > 假设你在上一步配置的链接为 `mysql+aiomysql://username:password@ip:port/database`

        > 则你在这一步配置的链接应为 `mysql://username:password@ip:port/database`

        > 你可能需要自行安装 `mysql` 的异步驱动 `aiomysql`

    - 其他数据库

        > 不知道捏，自己探索吧

        > 可查阅 SQLAlchemy 使用文档填写合适的链接

    <big>**如果你看不懂上述文本的话，看这个区块的第一行**</big>

## 启动机器人8

1. 启动 `mcl`
2. 进入bot目录下执行 `poetry run python main.py`

??? question "报错了怎么办？"

    如果你在前文使用了 `conda` 等虚拟环境，请保证其被正确激活

    如果是其他报错，请参考 [FAQ](../../FAQ/)

你应当见到类似如下界面：
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
2022-12-04 11:44:44.898 | DEBUG    | graia.saya:require:111 - require modules.self_contained.abbreviated_prediction
2022-12-04 11:44:44.913 | INFO     | graia.saya:require:134 - module loading finished: modules.self_contained.abbreviated_prediction
...
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:171 - 本次启动活动群组如下：
2022-01-04 23:45:13.263 | INFO     | SAGIRIBOT.Core.AppCore:bot_launch_init:173 - 群ID: 123456789     群名: xxxxxxx
...
```

其中 `...` 为省略的类似内容

现在，来试一试你的机器人吧！

## 后台运行

将窗口最小化即可
