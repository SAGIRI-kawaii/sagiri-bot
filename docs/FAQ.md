# 常见问题

!!! note "阅读前注意"
    
    如果未在此页面发现你想要的问题，可前往 [SAGIRI BOT官方交流群](https://jq.qq.com/?_wv=1027&k=9hfqo8AL) 或 github 提出 ISSUE，请附上程序报错信息。
    
    对于 `Java`（`mirai-console-loader`、`mirai-api-http` 相关）的报错，请务必截取到报错字段的开始部分
    
    对于 `Python`（`bot` 相关）的报错，请务必截取到报错字段的最后部分
    
    若你不知道报错中哪部分是真正有用的信息，请全部截取
    
    注意：若在QQ中询问问题时请不要直接将报错粘贴发送或者以 `txt` 文件等形式发送，请使用 `pastebin` 发送报错，或者发送截图

> ## Mysql / PostgreSQL 相关

目前只官方适配了 `sqlite`，使用 `Mysql` 以及 `PostgreSQL` 产生的bug可能会很多甚至会导致程序无法运行，若您需要稳定的运行请使用 `sqlite`

若您有好的解决方法可以PR，但请保证 `sqlite` 的兼容性

其他支持的数据库类型请查看 `sqlalchemy` 文档

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

> ## adapter down

若在运行时出现如下报错：
```text
2022-01-29 14:39:32.456 | WARNING  | graia.ariadne.app:daemon:1357 - daemon: adapter down, restart in 5.0s
2022-01-29 14:39:37.456 | INFO     | graia.ariadne.app:daemon:1359 - daemon: restarting adapter
2022-01-29 14:39:42.450 | CRITICAL | graia.ariadne.app:daemon:1343 - Timeout when connecting to mirai-api-http. Configuration problem?
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

请尝试重新粘贴配置，或更换端口，可能是有不可见字符混入配置文件

> ## Address in use

1. 检查是否开启了多个 `mirai-console-loader(mcl)`
2. 检查 `mirai-api-http(mah)` 使用的端口是否为常用端口，如 `80` `443` `8080` `8000` 等，该情况下请更换为非常用端口，如 `11451` `14514` 等
3. 检查 `mirai-api-http(mah)` 使用的端口是否被其他软件占用

> ## 内存占用问题

`SAGIRI-BOT` 需要至少 `1GB` 空闲内存以保证正常运行，若你的机器内存不足，可以选择删除 `sagiri_bot.handler.handlers.wordle`，代价是没有猜词功能，但可以减少 `400MB` 左右的内存消耗

> ## pip: ValueError: check_hostname requires server_hostname

关闭全局代理，重新执行命令

> ## Exception in thread "DefaultDispatcher-worker-2"...

- 方法一：检查 `mirai-api-http` 版本，若为 `2.5.0+` 请降级为 `2.4.0`
- 方法二：检查 `mirai-api-http` 版本，若为 `2.5.0+` 并且 `mirai` 版本低于 `2.11`，请将 `mirai` 升级到 `2.11+`

> ## java.lang.NoSuchMethodError: void kotlinx.serialization.internal.ObjectSerializer...

检查 `mirai-api-http` 版本，若为 `2.5.0+` 请降级为 `2.4.0`

详情请看 [mirai-api-http #568](https://github.com/project-mirai/mirai-api-http/issues/568)

> ## java.lang.illegalStateException: plugin 'net.mamoe.mirai-api-http' is already loaded and cannot be reloaded

前往 `mirai-console-loader` 的 `plugin` 文件夹下删除 `2.5.0` 版本的 `mirai-api-http` （以 `2.5.0.jar` 结尾的）（当且仅当 `mirai-api-http-v2.5.0` 的序列化bug未解决且正在降级至 `2.4.0` 时此条生效）

前往 `mirai-console-loader` 的 `plugin` 文件夹下删除重复的 `mirai-api-http` 插件 （常规状况）

> ## command "python" not found

<font color="red">Are you serious?</font>

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

> ## 代理相关

由于某些原因，此文档中不会涉及到代理的搭建、部署、使用等教程，请自行寻找教程