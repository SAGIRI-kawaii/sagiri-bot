# 配置文件

> ## 数据库配置

配置数据库链接（config.yaml - db_link）

- sqlite: sqlite+aiosqlite:///filename.db
- mysql: mysql+aiomysql://username:password@localhost:3306/dbname
- 注意：请自行安装对应的异步库，如aiomysql、aiosqlite等，且仅有sqlite可以保证正常使用

> ## config.yaml

用于存储机器人的各种配置，可随时进行更改

```yaml
# 必要数据及设置
bot_accounts: bot_accounts  # 机器人账号列表，例如 [qq1, qq2, ...]
default_account: default_account  # 默认机器人账号，从上方 bot_accounts 选一个即可
host_qq: host_qq  # 主人qq账号，默认权限等级 MASTER(4)
mirai_host: http://localhost:23456  # mirai-api-http 监听地址，请与 mirai-api-http 配置一致
verify_key: !!str 1234567890  # mirai-api-http 验证密钥，请与 mirai-api-http 配置一致
db_link: sqlite+aiosqlite:///data.db  # 数据库连接，若你不知道是什么则保持默认即可
web_manager_api: true # bot 启动是否自动启动 API（尚未实现）
web_manager_auto_boot: true # bot 启动是否自动管理后台（尚未实现）
proxy: proxy  # 代理地址，支持 http/socks5
auto_upgrade: false  # bot 启动是否自动更新（尚未测试）

# 图库相关
gallery:  # 请参看内置插件中图库的说明
  setu:
    path: path
    privilege: 1
    interval: 1
    need_proxy: true
  setu18:
    path: path
    privilege: 1
    interval: 10
    default_switch: false
  real:
    path: path
    privilege: 1
    interval: 1
  real_highq:
    path: path
    privilege: 1
    interval: 1
  bizhi:
    path: path
    privilege: 1
    interval: 1
  sketch:
    path: path
    privilege: 1
    interval: 1

# 个性化设置
commands: # 为支持的插件添加公共触发前缀，此举动会计算一个 prefix 和 alias 的笛卡尔积，并将其写入对应插件的 Twilight 中，具体请看
  default:  # 默认设置，对所有支持的插件应用
    prefix: []
    alias: []
# 可设置特定插件，但推荐使用 metadata.json 进行配置，并非所有插件都支持设置，具体请参看插件说明。例子如下
# modules.self_contained.abbreviated_prediction:
#   prefix: [/]
#   alias: [缩写]

# 功能相关
functions:
  tencent:
    secret_id: secret_id  # 腾讯云 secret_id（用于智能回复）
    secret_key: secret_key  # 腾讯云 secret_key（用于智能回复）
  saucenao_api_key: saucenao_api_key  # SAUCENAO API KEY（用于搜图）
  wolfram_alpha_key: wolfram_alpha_key  # WolframAlpha Key（用于科学计算）
  github:
    username: username  # GitHub 用户名（用于 GitHub 相关功能功能）
    token: token  # GitHub Token（用于 GitHub 相关功能功能）
  pica:
    username: username  # 哔咔漫画用户名
    password: password  # 哔咔漫画密码
    download_cache: true  # 哔咔漫画下载是否缓存
    search_cache: true  # 哔咔漫画搜索是否缓存
    daily_download_limit: 1  # 哔咔漫画每人每日下载漫画数量限制
    daily_search_limit: 1  # 哔咔漫画每人每日搜索漫画数量限制
    daily_random_limit: 1  # 哔咔漫画每人每日随机漫画数量限制
    daily_rank_limit: 1  # 哔咔漫画每人每日查看排行榜数量限制
    compress_password: i_luv_sagiri  # 哔咔漫画文件形式漫画解压密码
  bilibili:
    cookie: cookie  # BiliBili Cookie（用于查询 vtb 成分）
  stable_diffusion_api: stable_diffusion_api  # Stable Diffusion 地址，后端仅适配 https://github.com/SAGIRI-kawaii/stable-diffusion-webui-api，请自行部署（用于 AI 绘图）

# 日志相关
log_related:
  error_retention: 14 # 错误日志记录周期
  common_retention: 7 # common_retention

# 数据相关
data_related:
  lolicon_image_cache: true # 自动缓存获取到的 Lolicon Api 图片
  lolicon_data_cache: true # 自动缓存获取到的 Lolicon Api Json 数据
  network_data_cache: true
  data_retention: true

# 数据库相关，若不了解请不要修改这一部分，用于自定义engine参数
database_related:
  mysql:
    disable_pooling: false
    pool_size: 40
    max_overflow: 60
```

> ## saya_data.json

位置：`shared.models.saya_data`

!!! danger "使用前注意"

    注意，此模块不建议自行修改

配置格式：
```json
{
    switch: {
        channel_module: {
            group: {
                notice: bool,
                switch: bool
            }
        },
        ...
    },
    permission: {
        group_id: {
            member: level(int)
        },
        ...
    }
}
```

> ## metadata.json

此项用于自行修改插件信息/触发前缀，并非所有插件都支持，请在内置插件中查看说明

`metadata.json` 位于每一个内置插件的文件夹下，如 `sagiri-bot/modules/self_contained/abbreviated_prediction/metadata.json`，并且只会对其所处的插件起作用

!!! warning "配置时请注意"
    
    请注意避免出现多个模块触发词相同的情况（当然你也可以这样写，这是你的自由）

配置格式：
```json5
{
  "name": "AbbreviatedPrediction", // 插件名称，建议不要自行修改
  "version": "0.2", // 插件版本，建议不要自行修改
  "display_name": "缩写预测", // 插件显示名称，会在菜单中显示此名称
  "authors": ["SAGIRI-kawaii"], // 插件作者，建议不要自行修改
  "description": "一个获取英文缩写意思的插件", // 插件描述，建议不要自行修改
  "usage": ["在群中发送 `缩 内容` 即可"], // 插件使用方法，建议不要自行修改
  "example": ["/缩 abc"], // 插件使用示例，建议不要自行修改
  "icon": "", // 插件图标，使用 font-awesome，目前尚未实现
  "prefix": ["/", ""], // 插件触发前缀
  "triggers": ["缩", "缩写"], // 插件触发词
  "metadata": {  // 插件元数据，用于做一些配置
    "uninstallable": false, // 插件是否允许卸载
    "reloadable": true // 插件是否允许重载
    // 此处还可以存放一些插件所特有的配置项    
  }
}
```

上述配置会在插件载入时对 `prefix` 和 `triggers` 做一个笛卡尔积，即此时 `AbbreviatedPrediction` 支持的前缀有 `缩`，`缩写`，`/缩` 和 `/缩写`，你可以使用 `缩 abc`，`缩写 abc`，`/缩 abc`，`/缩写 abc` 来触发此功能