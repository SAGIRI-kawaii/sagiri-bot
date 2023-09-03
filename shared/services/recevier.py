import ujson
from contextlib import suppress
from sqlalchemy.exc import IntegrityError

from creart import it
from avilla.core import BaseAccount
from graia.broadcast import Broadcast
from avilla.core.exceptions import InvalidAuthentication
from avilla.standard.core.account import AccountAvailable

from shared.database import get_interface
from shared.utils.account import get_host
from shared.services.distribute import DistributeData, scene_dict
from shared.database.tables import PermissionLevel, UserPermission, User

bcc = it(Broadcast)


@bcc.receiver(AccountAvailable)
async def account_init(base_account: BaseAccount):
    with suppress(InvalidAuthentication):
        await it(DistributeData).add_account(base_account)
    db = get_interface()
    land = base_account.route["land"]
    # from loguru import logger
    async for scene in base_account.staff.query_entities(f"::{scene_dict[land]}"):
        scene = dict(scene.pattern)
        # logger.error(str(scene))
        for host in get_host(land):
            owner = ujson.dumps({**scene, "member": host})
            with suppress(IntegrityError):
                _ = await db.update_or_add(User(data_json=owner, user_permission=UserPermission(level=PermissionLevel.OWNER.value)))
