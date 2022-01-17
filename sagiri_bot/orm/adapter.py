mysql_adapter = {
    "pool_size": 40,
    "max_overflow": 60,
    "charset": "utf8mb4"
}


def get_adapter(url: str) -> dict:
    if url.startswith("mysql"):
        return mysql_adapter
    else:
        return {}
