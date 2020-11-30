import json


async def get_json_code(name: str):
    """
    get config from config.json

    Args:

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
    with open('json/json_message_code.json', 'r', encoding='utf-8') as f:  # 从json读配置
        configs = json.loads(f.read())
    if name in configs.keys():
        return configs[name]
    else:
        print("getJsonCode Error:%s" % name)
