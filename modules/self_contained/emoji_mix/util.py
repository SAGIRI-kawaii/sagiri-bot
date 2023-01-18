import json
import aiofiles
from pathlib import Path
from loguru import logger
from json import JSONDecodeError
from aiohttp import ClientSession
from typing import List, Tuple, Optional, Dict, Set

from creart import create

from shared.models.config import GlobalConfig

config = create(GlobalConfig)
proxy = config.proxy if config.proxy != "proxy" else ""
_JSON_LINK = (
    "https://raw.githubusercontent.com/xsalazar/"
    "emoji-kitchen/main/src/Components/emojiData.json"
)
_ASSETS = Path(__file__).parent / "assets"
_FILE = _ASSETS / "emojiData.json"
_UPDATE = _ASSETS / "update.json"
_KITCHEN: str = (
    "https://www.gstatic.com/android/keyboard/emojikitchen"
    "/{date}/u{left_emoji}/u{left_emoji}_u{right_emoji}.png"
)


async def _download_update():
    try:
        async with ClientSession() as session, session.get(
                _JSON_LINK, proxy=proxy
        ) as resp:
            data = await resp.json(content_type=None)
            async with aiofiles.open(_UPDATE, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data))
                logger.success("[EmojiMix] emojiData.json 下载完成")
    except Exception as e:
        logger.error(f"[EmojiMix] emojiData.json 下载失败: {e}")


def read_data(path: Path) -> List[Tuple[str, str, str]]:
    data: List[Tuple[str, str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        f_dict: Dict[str, List[Dict[str, str]]] = json.load(f)
        for pairs in f_dict.values():
            data.extend(
                (pair["leftEmoji"], pair["rightEmoji"], pair["date"]) for pair in pairs
            )
    return data


try:
    _MIX_DATA: List[Tuple[str, str, str]] = read_data(_UPDATE)
except (FileNotFoundError, JSONDecodeError, KeyError):
    logger.warning("[EmojiMix] emojiData.json 不存在或已损坏，使用回退数据")
    _UPDATE.unlink(missing_ok=True)
    _MIX_DATA: List[Tuple[str, str, str]] = read_data(_FILE)


def get_emoji(code_point: str) -> str:
    if "-" not in code_point:
        return chr(int(code_point, 16))
    emoji = code_point.split("-")
    return "".join(chr(int(i, 16)) for i in emoji)


def get_all_emoji() -> Set[str]:
    emoji = set()
    for left_emoji, right_emoji, _ in _MIX_DATA:
        emoji.add(get_emoji(left_emoji))
        emoji.add(get_emoji(right_emoji))
    return emoji


_ALL_EMOJI: Set[str] = get_all_emoji()


def emoji_to_codepoint(emoji: str) -> str:
    if len(emoji) == 1:
        return hex(ord(emoji))[2:]
    return "-".join(hex(ord(char))[2:] for char in emoji)


def get_mix_emoji_url(left_emoji: str, right_emoji: str) -> Optional[str]:
    left_emoji = emoji_to_codepoint(left_emoji)
    right_emoji = emoji_to_codepoint(right_emoji)
    for _left_emoji, _right_emoji, date in _MIX_DATA:
        if _left_emoji == left_emoji and _right_emoji == right_emoji:
            return _KITCHEN.format(
                date=date,
                left_emoji=left_emoji.replace("-", "-u"),
                right_emoji=right_emoji.replace("-", "-u"),
            )
        elif _left_emoji == right_emoji and _right_emoji == left_emoji:
            return _KITCHEN.format(
                date=date,
                left_emoji=right_emoji.replace("-", "-u"),
                right_emoji=left_emoji.replace("-", "-u"),
            )


def get_available_pairs(emoji: str) -> Set[str]:
    emoji = emoji_to_codepoint(emoji)
    pairs = set()
    for _left_emoji, _right_emoji, _ in _MIX_DATA:
        if _left_emoji == emoji:
            pairs.add(get_emoji(_right_emoji))
        elif _right_emoji == emoji:
            pairs.add(get_emoji(_left_emoji))
    return pairs
