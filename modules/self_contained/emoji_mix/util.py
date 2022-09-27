import re
from pathlib import Path
from typing import List, Tuple, Optional

ASSET_PATH: Path = Path(Path(__file__).parent, "assets")
DATA_JS_PATH: Path = Path(ASSET_PATH, "data.js")
EMOJI_URL: str = (
    "https://www.gstatic.com/android/keyboard/emojikitchen"
    "/{date}/u{emoji1}/u{emoji1}_u{emoji2}.png"
)


def read_data() -> List[Tuple[int, str, str]]:
    data: List[Tuple[int, str, str]] = []
    with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if match := re.findall(r"((?:[0-9a-f-]+/){3})", line):
                for _match in match:
                    date, emoji1, emoji2, _ = _match.split("/")
                    date = int(date, 16) + 20200000
                    data.append((date, str(emoji1), str(emoji2)))
    return data


def get_emoji(code_point: str) -> str:
    if "-" not in code_point:
        return chr(int(code_point, 16))
    emoji = code_point.split("-")
    return "".join(chr(int(i, 16)) for i in emoji)


def get_all_emoji() -> List[str]:
    emoji = set()
    for _, emoji1, emoji2 in MIX_DATA:
        emoji.add(get_emoji(emoji1))
        emoji.add(get_emoji(emoji2))
    return list(emoji)


def emoji_to_codepoint(emoji: str) -> str:
    if len(emoji) == 1:
        return hex(ord(emoji))[2:]
    return "-".join(hex(ord(char))[2:] for char in emoji)


def get_mix_emoji_url(emoji1: str, emoji2: str) -> Optional[str]:
    emoji1 = emoji_to_codepoint(emoji1)
    emoji2 = emoji_to_codepoint(emoji2)
    for date, _emoji1, _emoji2 in MIX_DATA:
        if _emoji1 == emoji1 and _emoji2 == emoji2:
            return EMOJI_URL.format(
                date=date,
                emoji1=emoji1.replace("-", "-u"),
                emoji2=emoji2.replace("-", "-u"),
            )
        elif _emoji1 == emoji2 and _emoji2 == emoji1:
            return EMOJI_URL.format(
                date=date,
                emoji1=emoji2.replace("-", "-u"),
                emoji2=emoji1.replace("-", "-u"),
            )


MIX_DATA = read_data()
ALL_EMOJI = get_all_emoji()
