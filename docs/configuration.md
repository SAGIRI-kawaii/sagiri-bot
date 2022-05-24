# 配置文件

> ## 数据库配置

- 配置数据库链接（config.yaml - db_link）
    - sqlite: sqlite+aiosqlite:///filename.db
    - mysql: mysql+aiomysql://username:password@localhost:3306/dbname
    - 注意：请自行安装对应的异步库，如aiomysql、aiosqlite等，且仅有sqlite可以保证正常使用

> ## config.yaml

用于存储机器人的各种配置，可随时进行更改
注意：所有路径的结尾都应该有斜杠，如："/bot/setuPath/" 或 "\bot\setuPath\" 等

|  参数名   | 说明  |
|  ----  | ----  |
| bot_qq  | 机器人的QQ号 |
| host_qq  | 主人的QQ号，默认权限等级4 |
| verify_key | mirai-api-http 的 verify_key，格式为 `!!str authKey` |
| mirai_host | 主机ip + mirai-api-http 的 port，一般在本地不用更改 |
| db_link | 数据库链接，可参看 [数据库配置](#_2) |
| web_manager_api | api是否启动（用于管理页面）\[暂未实现] |
| web_manager_auto_boot | 是否自动打开管理页面（webManagerApi为True时才起作用）\[暂未实现] |
| image_path | 图库路径，可自行添加图库，已给出六个自带图库 |
| setu | 二次元图片存储路径（绝对路径） |
| setu18 | 不对劲二次元图片存储路径（绝对路径） |
| real | 三次元图片存储路径（绝对路径） |
| real_highq | 高质量三次元图片存储路径（绝对路径） |
| wallpaper | 壁纸图片存储路径（绝对路径） |
| sketch | 线稿图片存储路径（绝对路径） |
| functions | 功能相关 |
| tencent-secret_id | 腾讯云secret_id（自行申请） |
| tencent-secret_key | 腾讯云secret_key（自行申请） |
| shadiao_app_name | shadiaoApp 应用名（自行申请） |
| saucenao_api_key | saucenao api key（自行获取） |
| wolfram_alpha_key | wolframAlphaKey，用于科学计算api调用 |
| github-username | github用户名 |
| github-token | github auth token |
| pica-username | 哔咔漫画用户名 |
| pica-password | 哔咔漫画密码 |
| pica-download_cache | 哔咔漫画缓存下载的漫画 |
| pica-search_cache | 哔咔漫画缓存搜索过的封面以减少下次搜索到此漫画的时长 |
| pica-daily_download_limit | 哔咔漫画每个账号每日下载上限个数 |
| pica-daily_search_limit | 哔咔漫画每个账号每日搜索上限次数 |
| pica-daily_random_limit | 哔咔漫画每个账号随机漫画上限次数 |
| pica-daily_rank_limit | 哔咔漫画每个账号每日获取排行榜上限次数 |
| pica-compress_password | 哔咔漫画文件上传密码 |
| log_related | 日志相关 |
| error_retention | 错误日志记录周期 |
| common_retention | 普通日志清空周期 |
| lolicon_image_cache | 是否缓存lolicon api所获取到的图片 |
| lolicon_data_cache | 是否缓存lolicon api所获取到的json数据 |
| network_data_cache | 自动保存各api的数据（暂未实现） |
| automatic_update | 自动更新（暂未实现） |
| data_retention | 退群后的数据处理 |
| database_related | 数据库相关（若不了解请不要修改这一部分，用于自定义engine参数） |

> ## saya_data.json

位置：`sagiri_bot.handler.required_module.saya_manager`

配置格式：
```text
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