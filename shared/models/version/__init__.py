import json
from abc import ABC
from typing import Type
from pathlib import Path
from pydantic import BaseModel

from creart import add_creator
from creart import exists_module
from creart.creator import AbstractCreator, CreateTargetInfo


class Version(BaseModel):
    bot_version: str = "Unknown"
    modules_version: dict[str, str] = {}

    def __init__(self):
        path = Path(__file__).parent / "version.json"
        if path.exists():
            with open(str(path), "r", encoding="utf-8") as r:
                data = json.load(r)
        else:
            data = {}
            with open(str(path), "w", encoding="utf-8") as w:
                w.write("{}")
        super().__init__(**data)

    def update_module_version(self, module: str, version: str):
        self.modules_version[module] = version
        self.save()

    def save(self):
        with open(str(Path(__file__).parent / "version.json"), "w", encoding="utf-8") as w:
            w.write(json.dumps(self.dict(), indent=4, ensure_ascii=False))


class VersionClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.models.version", "Version"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.models.version")

    @staticmethod
    def create(create_type: Type[Version]) -> Version:
        return Version()


add_creator(VersionClassCreator)
