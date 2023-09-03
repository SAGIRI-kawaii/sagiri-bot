import time
from abc import ABC
from typing import Type
from asyncio import Lock
from loguru import logger
from creart import add_creator, exists_module
from avilla.core import BaseAccount, Message, Selector
from creart.creator import AbstractCreator, CreateTargetInfo

from shared.utils.models import selector2pattern
from shared.utils.string import string_to_unique_number
scene_dict = {
    "qq": "group"
}

class DistributeData:
    """
    dict {
        land {
            scene: [account]
        }
    } 
    """
    data: dict[str, dict[str, list[str]]]
    inited_account: set[str]
    lock: Lock

    def __init__(self) -> None:
        self.data = {}
        self.inited_account = set()
        self.lock = Lock()
    
    async def add_account(self, base_account: BaseAccount):
        land = base_account.route["land"]
        account = base_account.route["account"]
        _ = await self.add_land(land)
        if land not in scene_dict:
            logger.error(f"暂不支持的协议：{land}")
            return
        async for scene in base_account.staff.query_entities(f"::{scene_dict[land]}"):
            scene = selector2pattern(scene)
            async with self.lock:
                if scene in self.data[land]:
                    self.data[land][scene].append(account)
                else:
                    self.data[land][scene] = [account]
        self.inited_account.add(account)
        logger.success(f"DistributeData 成功添加账号{account}<{land}>")
    
    async def add_land(self, land: str):
        if land not in self.data:
            async with self.lock:
                self.data[land] = {}
    
    async def add_scene(self, scene: Selector | str, land: str, account: str):
        if isinstance(scene, Selector):
            scene = selector2pattern(scene)
        _ = await self.add_land(land)
        if scene not in self.data[land]:
            self.data[land][scene] = [account]
    
    def need_distribute(self, land: str, scene: Selector | str) -> bool:
        if isinstance(scene, Selector):
            scene = selector2pattern(scene)
        if land in self.data and scene in self.data[land]:
            return len(self.data[land][scene]) > 1
        return False
    
    def get_index(self, base_account: BaseAccount, scene: Selector | str) -> int:
        land = base_account.route["land"]
        account = base_account.route["account"]
        scene = selector2pattern(scene) if isinstance(scene, Selector) else scene
        if land in self.data and scene in self.data[land] and account in self.data[land][scene]:
            return self.data[land][scene].index(account)
        print(self.data)
        raise ValueError
    
    def account_initialized(self, account: str):
        return account in self.inited_account

    async def execution_stop(self, base_account: BaseAccount, scene: Selector | str, message: Message | None = None) -> bool:
        scene = selector2pattern(scene) if isinstance(scene, Selector) else scene
        land = base_account.route["land"]
        account = base_account.route["account"]
        if land not in self.data:
            self.add_account(base_account)
            return True
        elif scene not in self.data[land]:
            await self.add_scene(scene, land, account)
            return True
        if message:
            return (string_to_unique_number(message.id) + int(time.mktime(message.time.timetuple()))) % len(self.data[land][scene]) != self.get_index(base_account, scene)
        else:
            return int(time.time()) % len(self.data[land][scene]) != self.get_index(base_account, scene)
    

class DistributeDataClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("shared.services.distribute", "DistributeData"),)

    @staticmethod
    def available() -> bool:
        return exists_module("shared.services.distribute")

    @staticmethod
    def create(create_type: Type[DistributeData]) -> DistributeData:
        return DistributeData()
    

add_creator(DistributeDataClassCreator)
