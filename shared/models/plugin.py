import ujson
from typing import Any
from pathlib import Path
from dataclasses import dataclass, field

from graia.saya.channel import ChannelMeta


@dataclass
class PluginMeta:
    name: str = field(default="")
    version: str = field(default="")
    display_name: str = field(default="")
    authors: list[str] = field(default_factory=list)
    description: str = field(default="")
    usage: list[str] = field(default_factory=list)
    example: list[str] = field(default_factory=list)
    maintaining: bool = field(default=False)
    icon: str = field(default="")
    prefix: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(cls, path: Path | str) -> "PluginMeta":
        if isinstance(path, str):
            path = Path(path)
        if path.is_file():
            path = path.parent
        metadata_path = path / "metadata.json"
        if metadata_path.exists():
            return cls(**ujson.loads(metadata_path.read_text(encoding="utf-8")))
        return cls()
    
    @classmethod
    def from_module(cls, module: str) -> "PluginMeta":
        paths = module.split('.')
        base_path = Path().cwd()
        for path in paths:
            base_path = base_path / path
        return cls.from_path(base_path)

    def gen_commands(self) -> list[str]:
        return [f"{p}{t}" for t in self.triggers for p in self.prefix]

    def to_saya_meta(self) -> ChannelMeta:
        return ChannelMeta(
            author=self.authors,
            name=self.name,
            version=self.version,
            license="APGLv3",
            description=self.description
        )
