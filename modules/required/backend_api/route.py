import psutil
import asyncio
from pathlib import Path
from websockets.exceptions import ConnectionClosedError
from fastapi import Depends, WebSocket, WebSocketDisconnect

from graiax.fastapi import route

from .utils import *
from .models import *
from .depends import *
from core import Sagiri
from shared.utils.files import read_file
from shared.models.saya_data import SayaData
from shared.models.public_group import PublicGroup
from shared.utils.string import is_url, get_log, clear_log
from shared.models.config import GlobalConfig, load_plugin_meta_by_module

saya = create(Saya)


@route.post("/login")
async def login(user: User):
    user.password = md5(user.password)
    if await has_account(user.username):
        if await account_legal(user.username, user.password):
            return GeneralResponse(data={"token": generate_token(user.username)})
        return GeneralResponse(code=202, message="username or password incorrect!")
    return GeneralResponse(code=201, message="user does not exist!")


@route.post("/saya/source")
async def get_saya_source(module: str, token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    path = module.replace(".", "/")
    if (p := Path.cwd() / (path + ".py")).exists():
        content = await read_file(p)
    elif (p := Path.cwd() / path).exists():
        content = await read_file(p / "__init__.py")
    else:
        return GeneralResponse(code=402, message=f"Module: {module} not found")
    return GeneralResponse(data={"source": content})


@route.get("/saya/installed_channels")
async def installed_channels(token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    channels = saya.channels
    modules = list(channels.keys())
    modules.sort()
    return GeneralResponse(
        data={
            module: {**channels[module].meta, "metadata": load_plugin_meta_by_module(module)}
            for module in modules
        }
    )


@route.get("/saya/not_installed_channels")
async def not_installed_channels(token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    modules = get_not_installed_channels()
    modules.sort()
    return GeneralResponse(data={"modules": modules})


@route.get("/saya/install")
async def get_install_channel(channel: str, token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    return install_channel(channel)


@route.get("/saya/uninstall")
async def get_uninstall_channel(channel: str, token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    return uninstall_channel(channel)


@route.get("/saya/reload")
async def get_reload_channel(channel: str, token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    return reload_channel(channel)


@route.get("/saya/modify_switch")
async def get_reload_channel(module: str, group_id: int, new_value: bool, token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    saya_data = create(SayaData)
    public_group = create(PublicGroup)
    if group_id not in public_group.data:
        return GeneralResponse(code=402, message=f"group {group_id} does not exist!")
    elif module not in saya_data.switch:
        return GeneralResponse(code=403, message=f"module {module} does not exist!")
    if new_value:
        saya_data.switch_on(module, group_id)
    else:
        saya_data.switch_off(module, group_id)
    return GeneralResponse()


@route.get("/group/list")
async def get_group_list(token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    public_group = create(PublicGroup)
    return GeneralResponse(
        data={
            group: {
                **(await Ariadne.current(list(public_group.data[group].keys())[0]).get_group(group)).dict(),
                "accounts": list(public_group.data[group].keys()),
                "permission": max_permission(list(public_group.data[group].values()))
            }
            for group in public_group.data
        }
    )


@route.get("/group/switch")
async def get_group_switch(token_valid: bool = Depends(certify_token), group_id: int | None = None):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    saya_data = create(SayaData)
    public_group = create(PublicGroup)
    if group_id and group_id not in public_group.data:
        return GeneralResponse(code=402, message=f"group {group_id} does not exist!")
    return GeneralResponse(
        data={
            module: saya_data.switch[module][str(group_id)]["switch"]
            for module in saya_data.switch
        } if group_id else {
            group: {
                module: saya_data.switch[module].get(str(group), {}).get("switch", False)
                for module in saya_data.switch
            }
            for group in public_group.data
        }
    )


@route.get("/group/detail")
async def get_group_detail(group_id: int, token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    public_group = create(PublicGroup)
    if group_id in public_group.data:
        group = await Ariadne.current(list(public_group.data[group_id].keys())[0]).get_group(group_id)
        group_config = await group.get_config()
        return GeneralResponse(data={**group_config.dict(), **group.dict()})
    return GeneralResponse(code=402, message=f"group {group_id} does not exist!")


@route.post("/group/send")
async def send_group_message(
    group_id: int, message: list, token_valid: bool = Depends(certify_token), account: int | None = None
):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    if account:
        if account in create(GlobalConfig).bot_accounts:
            app = Ariadne.current(account)
        else:
            return GeneralResponse(code=404, message=f"account {account} does not exist!")
    else:
        public_group = create(PublicGroup)
        if group_id in public_group.data:
            app = Ariadne.current(list(public_group.data[group_id].keys())[0])
        else:
            return GeneralResponse(code=402, message=f"group {group_id} does not exist!")
    message = parse_messagechain(message)
    if isinstance(message, MessageChain):
        _ = await app.send_group_message(group_id, message)
        return GeneralResponse()
    else:
        return GeneralResponse(code=403, data=message, message="missing parameters!")


@route.get("/friend/list")
async def get_friend_list(token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    return GeneralResponse(
        data={
            account: {
                friend.id: {**friend.dict()}
                for friend in await Ariadne.current(account).get_friend_list()
            } for account in create(GlobalConfig).bot_accounts
            if Ariadne.current(account).connection.status.available
        }
    )


@route.get("/friend/detail")
async def get_friend_detail(friend_id: int, token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    for account in create(GlobalConfig).bot_accounts:
        if Ariadne.current(account).connection.status.available:
            friends = await Ariadne.current(account).get_friend_list()
            for friend in friends:
                if friend.id == friend_id:
                    return GeneralResponse(data={**(await friend.get_profile()).dict(), **friend.dict()})
    return GeneralResponse(code=402, message=f"friend {friend_id} does not exist!")


@route.post("/friend/send")
async def send_group_message(
    friend_id: int, message: list, token_valid: bool = Depends(certify_token), account: int | None = None
):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    if account:
        if account in create(GlobalConfig).bot_accounts:
            app = Ariadne.current(account)
        else:
            return GeneralResponse(code=404, message=f"account {account} does not exist!")
    else:
        app = None
        for account in create(GlobalConfig).bot_accounts:
            if Ariadne.current(account).connection.status.available:
                friends = await Ariadne.current(account).get_friend_list()
                for friend in friends:
                    if friend.id == friend_id:
                        app = Ariadne.current(account)
                        break
        if not app:
            return GeneralResponse(code=402, message=f"friend {friend_id} does not exist!")
    message = parse_messagechain(message)
    if isinstance(message, MessageChain):
        _ = await app.send_friend_message(friend_id, message)
        return GeneralResponse()
    else:
        return GeneralResponse(code=403, data=message, message="missing parameters!")


@route.get("/sys/info")
async def get_sys_info(token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    mem = psutil.virtual_memory()
    core = create(Sagiri)
    config = create(GlobalConfig)
    return GeneralResponse(
        data={
            "memory": {"total": mem.total, "used": mem.used, "free": mem.free},
            "cpu": {
                "percent": psutil.cpu_percent(),
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq(),
            },
            "launch_time": time.mktime(core.launch_time.timetuple()),
            "storage": {
                path_name: f"{sum(Path(data['path'] / file).stat().st_size for file in Path(data['path']).glob('*'))}"
                if Path(data["path"]).exists() else ("网络路径" if is_url(data["path"]) else "无效本地/网络路径")
                for path_name, data in config.gallery.items()
            }
        }
    )


@route.get("/home")
async def get_home_info(token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    return GeneralResponse(
        data={
            "group_count": len(create(PublicGroup).data),
            "sent_count": create(Sagiri).sent_count,
            "received_count": create(Sagiri).received_count,
            "saya_count": len(create(Saya).channels),
            "talk_count": await get_talk_count_by_hour(),
            "account_count": len(await Ariadne.current().get_bot_list())
        }
    )


@route.get("/saya")
async def get_saya_info(token_valid: bool = Depends(certify_token)):
    if not token_valid:
        return GeneralResponse(code=401, message="invalid token!")
    channels = saya.channels
    modules = list(channels.keys())
    modules.sort()
    saya_data = create(SayaData)
    public_group = create(PublicGroup)
    modules_info = []
    temp_list = []
    for module in modules:
        temp_list.append({"module": module, **channels[module].meta, **load_plugin_meta_by_module(module).dict()})
        if len(temp_list) == 4:
            modules_info.append(temp_list)
            temp_list = []
    modules_info.append(temp_list)
    return GeneralResponse(
        data={
            "modules_info": modules_info,
            "groups": {
                group: {
                    "id": group,
                    "name": (await get_group_name(group)) or "Undefined",
                    "modules": {
                        module: saya_data.switch[module].get(str(group), {}).get("switch", False)
                        for module in saya_data.switch
                    }
                }
                for group in public_group.data
            }
        }
    )


@route.websocket("/log")
async def ws_log(websocket: WebSocket):
    await websocket.accept()
    clear_log()
    try:
        while True:
            if text := get_log():
                await websocket.send_json({"text": text})
            await asyncio.sleep(0.01)
    except (WebSocketDisconnect, ConnectionClosedError):
        clear_log()
        await websocket.close()
