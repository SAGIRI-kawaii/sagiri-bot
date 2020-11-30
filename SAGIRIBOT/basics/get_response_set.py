import json


def get_response_set() -> dict:
    """
    get response keywords from response_set.json

    Args:

    Examples:
        get_response_set("BotQQ")

    Returns:
        data
    """
    with open('json/response_set.json', 'r', encoding='utf-8') as f:  # 从json读配置
        response_set = json.loads(f.read())

    response_set["setu"] = set(response_set["setu"])
    response_set["real"] = set(response_set["real"])
    response_set["bizhi"] = set(response_set["bizhi"])
    return response_set
