from pydantic import BaseModel


class GlobalConfig(BaseModel):
    bot_qq: int
    host_qq: int
    mirai_host: str = "http://localhost:8080"
    verify_key: str = "1234567890"
    db_link: str = "sqlite+aiosqlite:///data.db"
    web_manager_api: bool = False
    web_manager_auto_boot: bool = False
    image_path: dict = {}
    proxy: str = "proxy"
    functions: dict = {
        "tencent": {
            "secret_id": "secret_id",
            "secret_key": "secret_key"
        },
        "saucenao_api_key": "saucenao_api_key",
        "lolicon_api_key": "lolicon_api_key",
        "wolfram_alpha_key": "wolfram_alpha_key"
    }
    log_related: dict = {
        "error_retention": 14,
        "common_retention": 7
    }
    data_related: dict = {
        "lolicon_image_cache": True,
        "network_data_cache": False,
        "automatic_update": False,
        "data_retention": False
    }
