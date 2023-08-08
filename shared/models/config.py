from kayaku import config
from typing import Literal, Optional
from dataclasses import dataclass, field, asdict


PROTOCOLS = Literal["mirai_api_http", "onebot_v11", "onebot_v12", "telegram", "discord", "qqguild", "red", "kook"]


@dataclass
class MiraiApiHttpAccount:
    url: str = "http://localhost:23456"
    verify_key: str = "1234567890"
    account: int = 0


@dataclass
class MiraiApiHttpConfig:
    host: int = field(default_factory=int)
    accounts: list[MiraiApiHttpAccount] = field(default_factory=lambda: [asdict(MiraiApiHttpAccount())])


@dataclass
class LoggerSetting:
    error_retention: int = 14
    common_retention: int = 7


@dataclass
class MysqlAdapter:
    disable_pooling: bool = False
    pool_size: int = 40
    max_overflow: int = 60


@dataclass
class DatabaseSetting:
    db_link: str = "sqlite+aiosqlite:///data.db"
    mysql: MysqlAdapter = field(default_factory=MysqlAdapter)


@config("config")
class GlobalConfig:
    protocols: list[PROTOCOLS] = field(default_factory=list)
    mirai_api_http: MiraiApiHttpConfig = field(default_factory=MiraiApiHttpConfig)
    logger_setting: LoggerSetting = field(default_factory=LoggerSetting)
    database_setting: DatabaseSetting = field(default_factory=DatabaseSetting)
    proxy: Optional[str] = None
