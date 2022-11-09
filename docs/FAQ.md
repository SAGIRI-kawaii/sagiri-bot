# 常见问题

!!! note "阅读前注意"
    
    如果未在此页面发现你想要的问题，可前往 [SAGIRI BOT官方交流群](https://jq.qq.com/?_wv=1027&k=9hfqo8AL) 或 github 提出 ISSUE，请附上程序报错信息。
    
    对于 `Java`（`mirai-console-loader`、`mirai-api-http` 相关）的报错，请务必截取到报错字段的开始部分
    
    对于 `Python`（`bot` 相关）的报错，请务必截取到报错字段的最后部分
    
    若你不知道报错中哪部分是真正有用的信息，请全部截取
    
    注意：若在QQ中询问问题时请不要直接将报错粘贴发送或者以 `txt` 文件等形式发送，请使用 `pastebin` 发送报错，或者发送截图

> ## Mysql / PostgreSQL 相关

目前只官方适配了 `SQLite`，使用 `MySQL` 以及 `PostgreSQL` 产生的bug可能会很多甚至会导致程序无法运行，若您需要稳定的运行请使用 `SQLite`

若您有好的解决方法可以PR，但请保证 `SQLite` 的兼容性

其他支持的数据库类型请查看 `SQLAlchemy` 文档

> ## PlayWright 报错

若出现如下报错：
```text
<class 'playwright._impl._api_types.Error'>: Executable doesn't exist at C:\Users\SAGIRI\AppData\Local\ms-playwright\chromium-956323\chrome-win\chrome.exe
╔═════════════════════════════════════════════════════════════════════════╗
║ Looks like Playwright Test or Playwright was just installed or updated. ║
║ Please run the following command to download new browsers:              ║
║                                                                         ║
║     playwright install                                                  ║
║                                                                         ║
║ <3 Playwright Team                                                      ║
╚═════════════════════════════════════════════════════════════════════════╝
```
请打开终端执行 `playwright install`

> ## alembic 报错

若出现如下报错（Windows）：
```text
'alembic' 不是内部或外部命令，也不是可运行的程序
或批处理文件。
```
- 先检查 `alembic` 是否安装成功，可使用 `pip list` 命令查看
- 使用 `anaconda` 创建虚拟环境，安装好依赖后在虚拟环境中启动（推荐）
- 将 `python/Scripts` 目录加入环境变量

> ## FAILED: Can't locate revision identified by 'xxx'

若出现以下信息：
```text
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
ERROR [alembic.util.messaging] Can't locate revision identified by 'xxx'
  FAILED: Can't locate revision identified by 'xxx'
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
ERROR [alembic.util.messaging] Can't locate revision identified by 'xxx'
  FAILED: Can't locate revision identified by 'xxx'
```

- 打开bot目录下的 `alembic` 文件夹，将其中 `versions` 清空（保留空文件夹）
- 打开数据库，删除名为 `alembic_version` 的数据表
- 重启机器人

??? question "不知道如何删除数据表？"

    你可以直接删除生成的数据库，**该操作会删除数据库的所有数据，如有需要，请提前备份**

    - SQLite

        > 假设你在 `config.yaml` 配置的链接为 `sqlite+aiosqlite:///data.db`

        > 则你可以直接删除生成的 `data.db`

    - MySQL

        > <del>都用 `MySQL` 了还不会删库？</del>

    - 其他数据库

        > 不知道捏，自己探索吧


> ## ClientConnectorError

若在运行时出现如下报错：
```text
2022-08-16 13:16:41.372 | WARNING  | graia.amnesia.builtins.aiohttp:connection_manage:277 - ClientConnectorError(ConnectionKey(host='127.0.0.1', port=8899, is_ssl=False, ssl=None, proxy=None, proxy_auth=None, proxy_headers_hash=None), ConnectionRefusedError(22, 'The remote computer refused the network connection', None, 1225, None))
2022-08-16 13:16:41.372 | WARNING  | graia.ariadne.connection.ws:_:79 - Websocket reconnecting in 5s...
2022-08-16 15:16:46.592 | WARNING | graia.ariadne.connection.ws::84 - Websocket reconnecting...
2022-08-16 15:16:46.626 | INFO | graia.ariadne.connection.ws::91 - Websocket connection closed
```
请执行以下几步：

1. 查看 `mirai-concole-loader(mcl)` 是否启动成功
2. 查看 `mirai-api-http(mah)` 是否启动成功
3. 查看 `mirai-api-http(mah)` 版本是否为 `2.x`（仅支持 `2.x` ）
4. 查看 `mirai-api-http(mah)` 是否配置正确，详细配置请看 [配置 mirai-api-http-v2](https://sagiri-kawaii.github.io/sagiri-bot/deployment/#mirai-api-http-v2_1)
5. 查看 `config.yaml` 中 `mirai_host` 项是否正确配置并与 `mah` 中配置相同
6. 查看是否在 `mirai-concole-loader(mcl)` 中登录了帐号
7. 若在 `mirai-concole-loader(mcl)` 中出现类似 `W/net.mamoe.mirai-api-http: USING INITIAL KEY, please edit the key` 的信息，请更换新的 `verifyKey` 后重启尝试
8. 查看是否同时启动了多个 `mirai-console-loader(mcl)`

> ## yamlDecodingException

若在运行时出现如下报错：
```text
2022-04-30 18:34:34 E/net.mamoe.mirai-api-http: net.mamoe.yamlkt.YamlDecodingException:There must be a COLON between class key and value but found null for 'setting'
```

请尝试重新粘贴 `mirai-api-http` 配置，或更换端口，可能是有不可见字符混入配置文件

> ## Address in use

1. 检查是否开启了多个 `mirai-console-loader(mcl)`
2. 检查 `mirai-api-http(mah)` 使用的端口是否为常用端口，如 `80` `443` `8080` `8000` 等，该情况下请更换为非常用端口，如 `11451` `14514` 等
3. 检查 `mirai-api-http(mah)` 使用的端口是否被其他软件占用

??? question "如何检查是否开启了多个 `mcl`？"

    - Windows

        > 打开任务管理器，检查是否有多个 Java 正在运行

    - Linux / macOS

        > 打开终端，输入 `ps -ef | grep "mcl" | grep -v "grep"`，检查是否有多个 `mcl` 正在运行

> ## 活动群组为空

如果启动时 `SAGIRI-BOT` 控制台中未显示任何活动群组，请确保在 `mcl` 启动并成功登录账号后再启动 `SAGIRI-BOT`

> ## 当前QQ版本过低

请参考 [mirai 论坛中的解决方案](https://mirai.mamoe.net/topic/223/%E6%97%A0%E6%B3%95%E7%99%BB%E5%BD%95%E7%9A%84%E4%B8%B4%E6%97%B6%E5%A4%84%E7%90%86%E6%96%B9%E6%A1%88)

> ## 内存占用问题

`SAGIRI-BOT` 需要至少 `700Mb` 空闲内存以保证正常运行，
如果你需要开启 `mockingbird` 和 `超分辨率` 组件，那占用将从 `700Mb` 提高到 `1.5Gb` 至少 (如果需要流畅跑完，可能还需要更多)  
若你的机器内存不足，可以加钱提升电脑配置。~~加钱加到9w8，1T内存抱回家~~

> ## pip: ValueError: check_hostname requires server_hostname

关闭全局代理，重新执行命令

> ## java.lang.illegalStateException: plugin 'net.mamoe.mirai-api-http' is already loaded and cannot be reloaded

前往 `mirai-console-loader` 的 `plugin` 文件夹下删除重复的 `mirai-api-http` 插件

> ## python: command not found

<font color="red">Are you serious?</font>

> ## [Errno 2] No such file or directory

如出现下列报错

```
C:\Users\SAGIRI>python mian.py
python: can't open file 'mian.py': [Errno 2] No such file or directory
```

[首都医科大学附属北京同仁医院眼科 科室电话010-58269911](https://www.trhos.com/Html/Departments/Main/Index_266.html)

> ## poetry: command not found

确保 `poetry` 已经安装，若未安装，请参考文档部署

若已安装，请检查 `poetry` 是否在 `PATH` 中，若不在，请手动添加

> ## /lib/x86_64-linux-gnu/libc.so.6: version GLIBC_2.28 not found

<font color="red">说明你没有认真看文档！</font>

查看 [mcl-installer #35](https://github.com/iTXTech/mcl-installer/issues/35)
    
使用命令 `curl -LJO https://ghproxy.com/github.com/iTXTech/mcl-installer/releases/download/f7ee211/mcl-installer-f7ee211-linux-amd64-musl`

> ## sqlalchemy.exc.ProgrammingError: (pymysql.err.ProgrammingError) (1146, "Table 'sagiri_bot.keyword_reply' doesn't exist")

该错误通常仅在首次启动或更换数据库时出现，并不会影响实际的功能使用。

相关 Issue：[#247](https://github.com/SAGIRI-kawaii/sagiri-bot/issues/247#issuecomment-1133041028)

> ## sqlalchemy.exc.DataError: (pymysql.err.DataError) (1366, "Incorrect string value: '\\xF0\\x9F\\x91\\x91' for column 'group_name' at row 1")

出现该错误的原因通常为使用非 `utf8mb4` 字符集的 `MySQL` 数据库。将数据库字符集更改为 `utf8mb4` 可解决该问题。

如在字符集已为 `utf8mb4` 的情况下出现该错误，请尝试在数据库链接后添加 `?charset=utf8mb4`，如 `mysql+aiomysql://user:pass@ip:port/sagiri_bot?charset=utf8mb4`

相关 Issue：[#40](https://github.com/SAGIRI-kawaii/sagiri-bot/issues/40) [#247](https://github.com/SAGIRI-kawaii/sagiri-bot/issues/247#issuecomment-1133041028)

> ## 下载速度问题

### git

- 可使用代理站：`https://ghproxy.com/`

- 使用示例：`git clone https://ghproxy.com/github.com/SAGIRI-kawaii/sagiri-bot.git`

### pip

- 可使用国内镜像源如清华园、豆瓣源等

- 使用示例：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

> ## sqlalchemy.exc.InternalError: (pymysql.err.InternalError) (1054, "Unknown column 'setting.avatar_func' in 'field list'")

请检查 `alembic.ini` 是否已正确配置

> ## iTXTech Soyuz 未安装 / SLF4J: Failed to load class "org.slf4j.impl.StaticLoggerBinder".

不会对正常使用造成影响，可忽略。

> ## playwright install-deps 失败

详见 [#229](https://github.com/SAGIRI-kawaii/sagiri-bot/issues/229) 与 [brillout/vite-plugin-ssr #283](https://github.com/brillout/vite-plugin-ssr/issues/283)

> ## pydantic.error_wrappers.ValidationError

请检查 config.yaml 是否配置正确。

出错位置应已在报错信息底部打印，比如以下错误代表 `bot_qq` 配置出错：

```text
bot_qq
    value is not a valid integer
(type=type_error.integer)
```

> ## 安装依赖时提示 ERROR: Could not open requirements.txt

请进入 bot 目录后再进行依赖安装

> ## 日志显示已发送图片，但是QQ无法显示

账号被腾讯风险控制，尝试开关设备锁、重新登录、或者登录满一至两周后再试。

> ## 消息时提示 graia.ariadne.exception.RemoteException

该类报错需要读取错误详情

* `MessageSvcPbSendMsg.Response.Failed(resultType=46, ...)`
    * 账号被冻结群消息发送，可手动登录机器人账号发送群消息解除冻结。

> ## macOS 部署教程

大部分可参考 Linux 部署教程

> ## 安卓下部署/运行出错

我猜你应该没有[看过这里](https://sagiri-kawaii.github.io/sagiri-bot/deployment/android/#_2)

> ## 代理相关

由于某些原因，此文档中不会涉及到代理的搭建、部署、使用等教程，请自行寻找教程