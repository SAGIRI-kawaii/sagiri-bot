import os
import psutil
import asyncio
import uvicorn
import datetime
import aiofiles
from typing import Union
from loguru import logger
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm.attributes import InstrumentedAttribute
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect

from graia.ariadne.event.message import MessageChain

from .models import User, GeneralResponse
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.orm.async_orm import Setting, orm
from .depends import generate_token, certify_token
from sagiri_bot.command_parse.commands import command_index
from .utils import md5, UserData, get_not_installed_channels, get_installed_channels, parse_messagechain

logs = []


def set_log(log_str: str):
    logs.append(log_str.strip())


user_data = UserData()

start_time = datetime.datetime.now()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
uninstall_modules = {}


@app.get("/token/get")
async def generate(token: str = Depends(generate_token)):
    return token


@app.get("/token/certify")
async def certify(valid: bool = Depends(certify_token)):
    return valid


@app.post("/register", response_model=GeneralResponse)
async def register(user: User):
    if user_data.has_user(user):
        return GeneralResponse(
            code=401,
            message="user_name already exist!"
        )
    user_data.add_user(user)
    return GeneralResponse()


@app.post("/login")
async def login(user: User, nonce: str):
    user.password = md5(user.password)
    if user_data.has_user(user):
        if user.password == user_data.get_user(user.user_name).password:
            return GeneralResponse(data={"token": generate_token(user.user_name, nonce)})
        else:
            return GeneralResponse(
                code=402,
                message="username or password incorrect!"
            )
    else:
        return GeneralResponse(
            code=401,
            message="user does not exist!"
        )


@app.get("/saya/source")
async def get_saya_source(module: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )
    path = module.replace('.', '/')
    if os.path.exists(f"{path}.py"):
        async with aiofiles.open(f"{path}.py", "r", encoding="utf-8") as fp:
            content = await fp.read()
    elif os.path.exists(path):
        async with aiofiles.open(f"{path}/__init__.py", "r", encoding="utf-8") as fp:
            content = await fp.read()
    else:
        return GeneralResponse(
            code=402,
            message=f"Module: {module} not found"
        )
    return GeneralResponse(
        data={
            "source": content
        }
    )


@app.get("/saya/installed_channels")
async def installed_channels(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )
    channels = AppCore.get_core_instance().get_saya_channels()
    modules = list(channels.keys())
    modules.sort()
    return GeneralResponse(
        data={
            module: {
                "name": channels[module]._name,
                "author": channels[module]._author,
                "description": channels[module]._description
            }
            for module in modules
        }
    )


@app.get("/saya/not_installed_channels")
async def not_installed_channels(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )
    modules = get_not_installed_channels()
    modules.sort()
    return GeneralResponse(data=[modules])


@app.get("/saya/install")
async def install_channel(channel: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )
    saya = AppCore.get_core_instance().get_saya()
    ignore = ["__init__.py", "__pycache__"]
    with saya.module_context():
        if channel in ignore:
            return GeneralResponse(
                code=202,
                message=f"module {channel} is on the ignore list"
            )
        try:
            saya.require(channel)
        except Exception as e:
            return GeneralResponse(
                code=500,
                data={"error": e},
                message=f"Module {channel} installation error"
            )
    return GeneralResponse()


@app.get("/saya/uninstall")
async def uninstall_channel(channel: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )
    saya = AppCore.get_core_instance().get_saya()
    loaded_channels = get_installed_channels()
    if channel not in loaded_channels:
        return GeneralResponse(
            code=402,
            message=f"module {channel} does not exist!"
        )
    with saya.module_context():
        try:
            saya.uninstall_channel(loaded_channels[channel])
        except Exception as e:
            return GeneralResponse(
                code=500,
                data={"error": e},
                message=f"Module {channel} uninstall error"
            )
    return GeneralResponse()


@app.get("/saya/reload")
async def reload_channel(channel: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )
    saya = AppCore.get_core_instance().get_saya()
    exceptions = {}
    loaded_channels = get_installed_channels()
    if channel not in loaded_channels:
        return GeneralResponse(
            code=403,
            message=f"module {channel} does not exist!"
        )
    with saya.module_context():
        try:
            saya.reload_channel(loaded_channels[channel])
        except Exception as e:
            return GeneralResponse(
                code=500,
                data={"error": e},
                message=f"Module {channel} reload error"
            )
    if not exceptions:
        return GeneralResponse()


@app.get("/group/list")
async def get_group_list(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )
    core = AppCore.get_core_instance()
    ariadne_app = core.get_app()
    loop = core.get_loop()
    return GeneralResponse(
        data={
            group.id: {
                "name": group.name,
                "accountPerm": group.accountPerm
            }
            for group in (asyncio.run_coroutine_threadsafe(ariadne_app.getGroupList(), loop).result())
        }
    )


@app.get("/group/detail")
async def get_group_detail(group_id: int, token: bool = Depends(certify_token)):
    if token:
        core = AppCore.get_core_instance()
        ariadne_app = core.get_app()
        loop = core.get_loop()
        if group := asyncio.run_coroutine_threadsafe(ariadne_app.getGroup(group_id), loop).result():
            group_config = asyncio.run_coroutine_threadsafe(group.getConfig(), loop).result()
            return GeneralResponse(
                data={
                    "name": group_config.name,
                    "announcement": group_config.announcement,
                    "confessTalk": group_config.confessTalk,
                    "allowMemberInvite": group_config.allowMemberInvite,
                    "autoApprove": group_config.autoApprove,
                    "anonymousChat": group_config.anonymousChat
                }
            )
        else:
            return GeneralResponse(
                code=402,
                message=f"group {group_id} does not exist!"
            )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.post("/group/send")
async def send_group_message(group_id: int, message: list, token: bool = Depends(certify_token)):
    if token:
        core = AppCore.get_core_instance()
        ariadne_app = core.get_app()
        loop = core.get_loop()
        message = parse_messagechain(message)
        if group := asyncio.run_coroutine_threadsafe(ariadne_app.getGroup(group_id), loop).result():
            if isinstance(message, MessageChain):
                asyncio.run_coroutine_threadsafe(
                    ariadne_app.sendGroupMessage(
                        group, message
                        # MessageChain(message)
                        # MessageChain.fromPersistentString(message).asSendable()
                    ),
                    loop
                ).result()
                return GeneralResponse()
            else:
                return GeneralResponse(
                    code=403,
                    data=message,
                    message="missing parameters!"
                )
        else:
            return GeneralResponse(
                code=402,
                message=f"group {group_id} does not exist!"
            )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.get("/group/setting/get")
async def get_group_setting(group_id: int, token: bool = Depends(certify_token)):
    if token:
        columns = {
            i: Setting.__dict__[i]
            for i in Setting.__dict__.keys() if isinstance(Setting.__dict__[i], InstrumentedAttribute)
        }
        column_names = list(columns.keys())
        column_names.sort()
        if result := await orm.fetchall(
            select(
                *([columns[name] for name in column_names])
            ).where(
                Setting.group_id == group_id
            )
        ):
            return GeneralResponse(data=result)
        else:
            return GeneralResponse(
                code=402,
                message=f"group {group_id} does not exist!"
            )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.get("/group/setting/modify")
async def modify_group_setting(group_id: int, column: str, value: Union[int, str], token: bool = Depends(certify_token)):
    if token:
        value = (True if value in ("True", "true") else False) if value in ("True", "true", "False", "false") else value
        columns = {
            i: Setting.__dict__[i]
            for i in Setting.__dict__.keys() if isinstance(Setting.__dict__[i], InstrumentedAttribute)
        }
        if column in columns:
            if await orm.fetchone(select(Setting).where(Setting.group_id == group_id)):
                if command_index[column].is_valid(value):
                    try:
                        await orm.insert_or_update(Setting, [Setting.group_id == group_id], {column: value})
                    except Exception as e:
                        logger.exception("")
                        return GeneralResponse(
                            code=500,
                            message=str(e)
                        )
                    return GeneralResponse()
                else:
                    valid_values = command_index[column].valid_values
                    valid_values = [str(i) for i in valid_values]
                    return GeneralResponse(
                        code=405,
                        message=f"invalid value for column {column}: {value}! "
                                f"valid values for {column}: {', '.join(valid_values)}"
                    )
            else:
                return GeneralResponse(
                    code=402,
                    message=f"group {group_id} does not exist!"
                )
        else:
            return GeneralResponse(
                code=403,
                message=f"invalid column name: {column}! valid columns: {', '.join(columns.keys())}"
            )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.get("/friend/list")
async def get_friend_list(token: bool = Depends(certify_token)):
    if token:
        core = AppCore.get_core_instance()
        ariadne_app = core.get_app()
        loop = core.get_loop()
        return GeneralResponse(
            data={
                friend.id: {
                    "nickname": friend.nickname,
                    "remark": friend.remark
                }
                for friend in (asyncio.run_coroutine_threadsafe(ariadne_app.getFriendList(), loop).result())
            }
        )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.get("/friend/detail")
async def get_friend_detail(friend_id: int, token: bool = Depends(certify_token)):
    if token:
        core = AppCore.get_core_instance()
        ariadne_app = core.get_app()
        loop = core.get_loop()
        if friend := asyncio.run_coroutine_threadsafe(ariadne_app.getFriend(friend_id), loop).result():
            friend_profile = asyncio.run_coroutine_threadsafe(friend.getProfile(), loop).result()
            return GeneralResponse(
                data={
                    "nickname": friend_profile.nickname,
                    "email": friend_profile.email,
                    "age": friend_profile.age,
                    "level": friend_profile.level,
                    "sign": friend_profile.sign,
                    "sex": friend_profile.sex
                }
            )
        else:
            return GeneralResponse(
                code=402,
                message=f"friend {friend_id} does not exist!"
            )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.post("/friend/send")
async def send_friend_message(friend_id: int, message: list, token: bool = Depends(certify_token)):
    if token:
        core = AppCore.get_core_instance()
        ariadne_app = core.get_app()
        loop = core.get_loop()
        message = parse_messagechain(message)
        if friend := asyncio.run_coroutine_threadsafe(ariadne_app.getFriend(friend_id), loop).result():
            if isinstance(message, MessageChain):
                asyncio.run_coroutine_threadsafe(
                    ariadne_app.sendFriendMessage(
                        friend, message
                    ),
                    loop
                ).result()
                return GeneralResponse()
            else:
                return GeneralResponse(
                    code=403,
                    data=message,
                    message="missing parameters!"
                )
        else:
            return GeneralResponse(
                code=402,
                message=f"friend {friend_id} does not exist!"
            )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.get("/sys/info")
async def get_sys_info(token: bool = Depends(certify_token)):
    if token:
        mem = psutil.virtual_memory()
        return GeneralResponse(
            data={
                "memory": {
                    "total": mem.total,
                    "used": mem.used,
                    "free": mem.free
                },
                "cpu": {
                    "percent": psutil.cpu_percent(),
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq()
                }
            }
        )
    else:
        return GeneralResponse(
            code=401,
            message="invalid token!"
        )


@app.websocket_route("/log")
async def ws_log(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if logs:
                await websocket.send_text(logs.pop(0))
    except WebSocketDisconnect:
        await websocket.close()


def run_api_server():
    logger.info("starting api server")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
