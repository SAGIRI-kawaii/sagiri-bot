from typing import Type, TypeVar, Optional

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import MatchResult


T = TypeVar("T")


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_type(message: MessageChain, res_type: Type[T], default_value: Optional[T] = None) -> T:
    message = message.display.strip()
    try:
        return res_type(message)
    except ValueError:
        return default_value


def parse_match_type(match: MatchResult, res_type: Type[T], default_value: Optional[T] = None) -> T:
    return parse_type(match.result, res_type, default_value) if match.matched else default_value
