from collections.abc import Callable
from typing import Any, Literal

from sqlalchemy.engine.interfaces import IsolationLevel, _ExecuteOptions, _ParamStyle
from sqlalchemy.log import _EchoFlagType
from sqlalchemy.pool import Pool, _CreatorFnType, _CreatorWRecFnType, _ResetStyleArgType
from typing_extensions import TypedDict


class EngineOptions(TypedDict, total=False):
    connect_args: dict[Any, Any]
    convert_unicode: bool
    creator: _CreatorFnType | _CreatorWRecFnType
    echo: _EchoFlagType
    echo_pool: _EchoFlagType
    enable_from_linting: bool
    execution_options: _ExecuteOptions
    future: Literal[True]
    hide_parameters: bool
    implicit_returning: Literal[True]
    insertmanyvalues_page_size: int
    isolation_level: IsolationLevel
    json_deserializer: Callable[..., Any]
    json_serializer: Callable[..., Any]
    label_length: int | None
    logging_name: str
    max_identifier_length: int | None
    max_overflow: int
    module: Any | None
    paramstyle: _ParamStyle | None
    pool: Pool | None
    poolclass: type[Pool] | None
    pool_logging_name: str
    pool_pre_ping: bool
    pool_size: int
    pool_recycle: int
    pool_reset_on_return: _ResetStyleArgType | None
    pool_timeout: float
    pool_use_lifo: bool
    plugins: list[str]
    query_cache_size: int
    use_insertmanyvalues: bool
    kwargs: dict[str, Any]
