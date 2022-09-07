from pathlib import Path
from typing import List, Literal

from graia.ariadne.message.parser.twilight import UnionMatch

from shared.models.config import load_plugin_meta, get_plugin_config


def get_command_match(prefix: List[str], alias: List[str]) -> List[str]:
    result = []
    for p in prefix:
        result.extend(p + a for a in alias)
    return result


def get_command(
    path: Path | str,
    module: str,
    return_type: Literal["union_match", "list"] = "union_match"
) -> UnionMatch | List[str]:
    plugin_meta = load_plugin_meta(path)
    plugin_config = get_plugin_config(module)
    prefix = plugin_config.get("prefix")
    alias = plugin_config.get("alias")
    prefix = list(set(prefix + plugin_meta.prefix))
    alias = list(set(alias + plugin_meta.triggers))
    if return_type == "union_match":
        return UnionMatch(*get_command_match(prefix, alias))
    else:
        return get_command_match(prefix, alias)
