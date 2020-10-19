import json


async def get_config(config: str):
    """
    get config from config.json

    Args:
        config: Config name to query
            config list:
                BotQQ: Bot QQ number
                HostQQ: Host QQ number
                authKey: Authkey linked to mirai_http_api
                miraiHost: Host address of mirai_http_api
                dbHost: Host address of MySQL database
                dbName: Database name
                dbUser: Database account name
                dbPass: Database password of dbUser
                setuPath: HPics gallery path(animate)
                realPath: HPics gallery path(real person)

    Examples:
        get_config("BotQQ")

    Returns:
        Return parameter type list:
            BotQQ: int
            HostQQ: int
            authKey: str
            miraiHost: str
            dbHost: str
            dbName: str
            dbUser: str
            dbPass: str
            setuPath: str
    """
    with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
        configs = json.loads(f.read())
    if config in configs.keys():
        return configs[config]
    else:
        print("getConfig Error:%s" % config)


