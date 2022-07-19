# 项目部署

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

    当部署出现问题时，请检查是否按文档顺序进行，如出现问题可前往 [FAQ](https://sagiri-kawaii.github.io/sagiri-bot/FAQ/) 寻找，如果没有找到原因可以前往 [SAGIRI BOT官方交流群](https://jq.qq.com/?_wv=1027&k=9hfqo8AL) 询问或在 github 提出 ISSUE

## 安装java

### 使用 [mcl-installer](https://github.com/iTXTech/mcl-installer) 进行安装（小白友好）
```text
$ cd 你想要安装 iTXTech MCL 的目录
$ curl -LJO https://github.com/iTXTech/mcl-installer/releases/download/v1.0.4/mcl-installer-1.0.4-linux-amd64 # 如果是macOS，就将链接中的 linux 修改为 macos
$ 若链接不上或速度过低可使用代理站: curl -LJO https://ghproxy.com/github.com/iTXTech/mcl-installer/releases/download/v1.0.4/mcl-installer-1.0.4-linux-amd64
$ chmod +x mcl-installer-1.0.4-linux-amd64
$ ./mcl-installer-1.0.4-linux-amd64
```
- 你应当见到如下输出：

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

!!! note "注意"

    若你在运行 `./mcl-installer-1.0.4-linux-amd64` 时出现如下报错：
    
    `./mcl-installer-1.0.4-linux-amd64: /lib/x86_64-linux-gnu/libc.so.6: version GLIBC_2.28 not found (required by ./mcl-installer-1.0.4-linux-amd64)`
    
    请查看 [mcl-installer #35](https://github.com/iTXTech/mcl-installer/issues/35)
    
    使用命令 `curl -LJO https://ghproxy.com/github.com/iTXTech/mcl-installer/releases/download/f7ee211/mcl-installer-f7ee211-linux-amd64-musl`

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

- 使用 `Ctrl + C` 退出 `mirai-console`

### 自行安装
搜索引擎会告诉你一切，搜索关键词：`Linux java安装`

## 安装[mirai](https://github.com/mamoe/mirai)

### 使用 [mcl-installer](https://github.com/iTXTech/mcl-installer) 进行安装（推荐）

若在安装java时已使用 `mcl-installer` 安装并配置完成，则可跳过此步

### 使用 [mirai-console-loader(mcl)](https://github.com/iTXTech/mirai-console-loader) 进行安装

- 打开mcl的 [release](https://github.com/iTXTech/mirai-console-loader/releases) 页面，点击 `mcl-x.x.x.zip` 下载最新版本
- 下载后解压并运行 `./mcl`

### 自行安装

- 这就靠你自己咯（
- mirai项目地址在这个页面有哦~自己找找吧~

## 安装 [mirai-api-http-v2](https://github.com/project-mirai/mirai-api-http)

### 通过 [mirai-console-loader(mcl)](https://github.com/iTXTech/mirai-console-loader) 进行安装（推荐）

- 按照 `mirai-api-http` 的 `README`，运行 `./mcl --update-package net.mamoe:mirai-api-http --channel stable-v2 --type plugin`
- 切换 `mirai-console-loader` 的 `repo`，运行 `./mcl --mrm-use forum`（当出现网络报错时执行）
- 启动 `mcl` 完成自动更新和启动

!!! warning "安装注意"
    
    若出现如 `[ERROR] The local file "net.mamoe:mirai-api-http" is still corrupted, plase check the network` 的报错，请尝试使用以下任一方法：
    
    - 使用下方自行安装方法，
    - 尝试更改 `MCL` 的 `repo`，具体请查看 [mcl-无法使用的相关解决方法](https://mirai.mamoe.net/topic/1084/mcl-%E6%97%A0%E6%B3%95%E4%BD%BF%E7%94%A8%E7%9A%84%E7%9B%B8%E5%85%B3%E8%A7%A3%E5%86%B3%E6%96%B9%E6%B3%95-2022-3-25) 
    - 尝试更改 `MCL` 的 `config.json`，打开后更改 `package` 中 `id` 为 `net.mamoe:mirai-api-http` 的字典的 `version` 值为 `2.4.0`，并将下方 `versionLocked` 改为 `true`
    
    当启动后出现如下方的消息才算安装并启动成功
    
    ```text
    2022-04-30 12:20:17 I/Mirai HTTP API: ********************************************************
    2022-04-30 12:20:17 I/http adapter: >>> [http adapter] is listening at http://localhost:23456
    2022-04-30 12:20:17 I/ws adapter: >>> [ws adapter] is listening at ws://localhost:23456
    2022-04-30 12:20:17 I/Mirai HTTP API: Http api server is running with verifyKey: 1234567890
    2022-04-30 12:20:17 I/Mirai HTTP API: adaptors: [http,ws]
    2022-04-30 12:20:17 I/Mirai HTTP API: ********************************************************
    ```

### 自行安装

- 打开 [mirai-http-api-release](https://github.com/project-mirai/mirai-api-http/releases/latest)，下载其中名为 `mirai-api-http-v2.x.x.mirai.jar` 的文件
- 将下载好的文件放入 `mcl/plugins` 文件夹
- 启动 `mcl` 完成自动更新和启动

## 配置 [mirai-api-http-v2](https://github.com/project-mirai/mirai-api-http)

- 打开 `MCL/config/net.mamoe.mirai-api-http/setting.yml`
- 若无此文件请检查 `mcl` 是否被成功添加并且添加后启动过一次 `mcl`，若没有请完成前文所述步骤再进行此步骤

内容如下：
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

### 配置自动登录

!!!warning "注意"

    为防止因填入不当数据导致无法启动 mirai-console-loader (MCL) 的问题，**建议在部署时通过 mirai-console-loader (MCL) 内建的 `autoLogin` 指令配置自动登录**，而非直接修改 Console 配置文件

#### 使用 /autoLogin 配置自动登录（推荐）

在 mirai-console-loader (MCL) 登录完成后，输入 `/autoLogin add <你的QQ号> <你的QQ密码>` 并回车，应该会显示 `已成功添加 '<你的QQ号>'`

#### 修改 Console 配置文件实现自动登录（不推荐）

!!!warning "仅可在 mirai-console-loader (MCL) 已关闭的情况下更改配置文件"

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

!!!note "如何实现手机和 mirai 同时在线？"

    可通过更改登录协议实现，操作如下：

    在已配置自动登录后，输入 `/autoLogin setConfig <你的QQ号> protocol IPAD`

    指令中的 `IPAD` 可更换为其他登录协议，如 `ANDROID_PAD` `ANDROID_WATCH` 等，推荐使用 `IPAD` 登录协议以防止出现部分功能无法使用的情况

    注意：更改协议后需要重启 `mcl` 才可生效

    > 什么？你想手机平板手表电脑和 mirai 同时在线？

    > 我的建议是，为什么不问问万能的神奇海螺呢？

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

## 安装python

!!!note "部分主流 linux 发行版已内置python"

    可直接在终端输入 `python` 并按 `tab` 键检查是否已安装 python

    注意，部分系统内置的 python 版本可能低于 sagiri-bot 的最低需求版本(3.8)，如直接运行 `python --version` 时显示的版本低于 3.8，则需要继续进行本区块的安装流程

### 使用 MiniConda

- 下载安装包，在终端里输入 `wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh`
- 下载完成后，在终端里输入 `chmod 777 Miniconda3-latest-Linux-x86_64.sh` ，赋予安装包权限
- 运行 `sh Miniconda3-latest-Linux-x86_64.sh` ，完成安装
- 输入 `conda --version`，若正常输出版本则安装成功，可直接跳过下方配置环境变量步骤
- 配置环境变量
    - 在终端输入 `vim ~/.bashrc`
    - 在文件中添加 `export PATH=/path_to_anaconda/miniconda3/bin:$PATH`，例如我的Anaconda安装路径为 `/home/user/miniconda3`，则要添加的项为 `export PATH=/home/user/miniconda3/bin:$PATH`
    - 点击 `ESC` 键，输入 `:wq` 保存并退出vim编辑器
    - 在终端里输入 `source ~/.bashrc` ，更新环境变量
    - 再次输入 `conda --version`，此时应该已经可以正常输出版本
- 创建虚拟环境（可选但推荐）
    - 在终端里输入 `conda create -n your_env_name python=3.8`，其中 `your_env_name` 为你要创建的环境名，可自定义，python版本 >= 3.8 即可，可自行安装其他版本
    - 等待程序询问是否安装，直接回车即可
    - 安装完毕后输入 `conda activate your_env_name` 即可激活虚拟环境

### 自行安装

搜索引擎会告诉你一切，搜索关键词：`Linux python3.8安装`，注意，安装的python版本必须大于等于3.8！

## 下载 SAGIRI-BOT

- 打开终端，进入你想要下载的目标文件夹
- 输入 `git clone https://github.com/SAGIRI-kawaii/sagiri-bot.git`
- 等待下载完成

!!!note "什么？你问我为什么这个一输进去就报错？"

    <del>不会还有人的 linux 发布版没安装 `git` 吧？</del>可输入 `sudo apt install git` 安装 `git` 命令，然后再运行克隆命令

    `apt` 可替换为其他发行版的安装命令，如 `yum`、`dnf`、`pacman` 等

!!!note "什么？你问我太慢怎么办？"
    
    我的建议是，找一台可以快速链接 `github` 的机器下载再传过来
    
    或者你可以使用代理站：`git clone https://ghproxy.com/github.com/SAGIRI-kawaii/sagiri-bot.git`

!!!danger "***真的非常不建议***直接从 GitHub 下载仓库的 zip 或 tar 文件"

    大部分情况下，直接使用 zip 或 tar 文件进行安装无法通过 `git pull` 进行更新，即使用该方法，可能无法正常更新且可能有稳定性问题

    <del>如果是因为直接下的 zip 或 tar 文件而且一直没更新导致的问题，就不要跑来群里或者发 issue 问了</del>

## 配置python虚拟环境

!!!question "为什么要配置python虚拟环境？"

    防止出现依赖混乱或冲突等问题，常用的虚拟环境有 `conda` `venv` `poetry` 等

    <del>当然你也可以不配置，但是如果你不配置而且服务器上还有其他的一些python项目，那么你的程序可能会出现一些问题</del>

### 使用 anaconda

- 若你在安装python时使用的是安装 Anaconda 的方法并且 `自带python版本>=3.8` 或已经配置好虚拟环境可跳过此项
- 在终端里输入 `conda activate your_env_name` 进入虚拟环境（Anaconda自带版本 >= 3.8可忽略此步骤，但推荐使用虚拟环境以防止出现依赖混乱冲突的情况，若你还没有创建虚拟环境并且自带python版本不符合条件，请查看上方创建虚拟环境）
- 激活成功后进入bot所在目录，运行 `pip install -r requirements.txt` 即可


### 使用 poetry

!!!warning "此处将默认你已经安装了 `poetry`"

- 终端中进入bot所在目录，运行 `poetry install` 即可

!!!note "`Resolving dependencies...` 部分耗时过长？"
    
    不用慌张！<del>这是技术性调整</del>

    可能是因为你的网络不稳定，或者你的网络环境不符合要求，导致 `poetry install` 失败，请尝试使用 `pip` 安装依赖

    > 大概需要多久安装成功呢？

    > 截至这个区块编写完成，已知的最长用时是 20 分钟。

### 直接使用 pip

- 终端中进入bot所在目录，运行 `pip install -r requirements.txt` 即可

## 配置config

- 打开 `config_demo.yaml`
- 按文件中注释更改
- 将文件更名为 `config.yaml`

!!!note "不知道怎么改数据库链接？"

    **大部分情况下保持不变即可。**

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

- 运行一次bot ( `python main.py` )，bot应会自动退出
- 在目录下寻找 `alembic.ini` 文件并打开
- 将其中 `sqlalchemy.url` 项更换为自己的连接（不需注明引擎否则会报错）（如 `sqlite:///data.db`）

!!!note "不知道什么是引擎？"

    **如果你在上一步保持不变，这一步跳过即可。**

    - SQLite

        > 假设你在上一步配置的链接为 `sqlite+aiosqlite:///data.db`

        > 则你在这一步配置的链接应为 `sqlite:///data.db`

    - MySQL

        > 假设你在上一步配置的链接为 `mysql+aiomysql://username:password@ip:port/database`

        > 则你在这一步配置的链接应为 `mysql://username:password@ip:port/database`

    - 其他数据库

        > 不知道捏，自己探索吧

        > 可查阅 SQLAlchemy 使用文档填写合适的链接

    **如果你看不懂上述文本的话，看这个区块的第一行**

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

## 后台运行

可使用 `bg` `screen` `tmux` `nohup` 等方法实现后台运行，此处不作过多阐述。