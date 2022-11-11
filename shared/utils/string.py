import re
from typing import Match

logs = []


def set_log(log_str: str):
    logs.append(log_str.strip())


def get_log() -> str | None:
    return logs.pop(0) if logs else None


def clear_log():
    global logs
    logs = []


def is_url(path: str) -> Match[str] | None:
    url_pattern = r"((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"
    json_url_pattern = r"json:([\w\W]+\.)+([\w\W]+)\$" + url_pattern
    return re.match(url_pattern, path) or re.match(json_url_pattern, path)
