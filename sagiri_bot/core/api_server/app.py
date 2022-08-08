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

from creart import create
from graia.saya import Saya
from graia.ariadne import Ariadne
from graia.ariadne.event.message import MessageChain

from .models import User, GeneralResponse
from sagiri_bot.orm.async_orm import Setting, orm
from .depends import generate_token, certify_token
from sagiri_bot.command_parse.commands import command_index
from .utils import (
    md5,
    UserData,
    get_not_installed_channels,
    get_installed_channels,
    parse_messagechain,
)

logs = []
saya = create(Saya)
loop = create(asyncio.AbstractEventLoop)


def set_log(log_str: str):
    logs.append(log_str.strip())


user_data = UserData()

start_time = datetime.datetime.now()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        return GeneralResponse(code=401, message="user_name already exist!")
    user_data.add_user(user)
    return GeneralResponse()


@app.post("/login")
async def login(user: User, nonce: str):
    user.password = md5(user.password)
    if user_data.has_user(user):
        if user.password == user_data.get_user(user.user_name).password:
            return GeneralResponse(
                data={"token": generate_token(user.user_name, nonce)}
            )
        else:
            return GeneralResponse(code=402, message="username or password incorrect!")
    else:
        return GeneralResponse(code=401, message="user does not exist!")


@app.get("/saya/source")
async def get_saya_source(module: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    path = module.replace(".", "/")
    if os.path.exists(f"{path}.py"):
        async with aiofiles.open(f"{path}.py", "r", encoding="utf-8") as fp:
            content = await fp.read()
    elif os.path.exists(path):
        async with aiofiles.open(f"{path}/__init__.py", "r", encoding="utf-8") as fp:
            content = await fp.read()
    else:
        return GeneralResponse(code=402, message=f"Module: {module} not found")
    return GeneralResponse(data={"source": content})


@app.get("/saya/installed_channels")
async def installed_channels(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    channels = saya.channels
    modules = sorted(channels.keys())
    return GeneralResponse(
        data={
            module: {
                "name": channels[module]._name,
                "author": channels[module]._author,
                "description": channels[module]._description,
            }
            for module in modules
        }
    )


@app.get("/saya/not_installed_channels")
async def not_installed_channels(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    modules = get_not_installed_channels()
    modules.sort()
    return GeneralResponse(data=[modules])


@app.get("/saya/install")
async def install_channel(channel: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    ignore = ["__init__.py", "__pycache__"]
    with saya.module_context():
        if channel in ignore:
            return GeneralResponse(
                code=202, message=f"module {channel} is on the ignore list"
            )
        try:
            saya.require(channel)
        except Exception as e:
            return GeneralResponse(
                code=500,
                data={"error": e},
                message=f"Module {channel} installation error",
            )
    return GeneralResponse()


@app.get("/saya/uninstall")
async def uninstall_channel(channel: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    loaded_channels = get_installed_channels()
    if channel not in loaded_channels:
        return GeneralResponse(code=402, message=f"module {channel} does not exist!")
    with saya.module_context():
        try:
            saya.uninstall_channel(loaded_channels[channel])
        except Exception as e:
            return GeneralResponse(
                code=500, data={"error": e}, message=f"Module {channel} uninstall error"
            )
    return GeneralResponse()


@app.get("/saya/reload")
async def reload_channel(channel: str, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    exceptions = {}
    loaded_channels = get_installed_channels()
    if channel not in loaded_channels:
        return GeneralResponse(code=403, message=f"module {channel} does not exist!")
    with saya.module_context():
        try:
            saya.reload_channel(loaded_channels[channel])
        except Exception as e:
            return GeneralResponse(
                code=500, data={"error": e}, message=f"Module {channel} reload error"
            )
    if not exceptions:
        return GeneralResponse()


@app.get("/group/list")
async def get_group_list(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    ariadne_app = Ariadne.current()
    return GeneralResponse(
        data={
            group.id: {"name": group.name, "account_perm": group.account_perm}
            for group in (
                asyncio.run_coroutine_threadsafe(
                    ariadne_app.get_group_list(), loop
                ).result()
            )
        }
    )


@app.get("/group/detail")
async def get_group_detail(group_id: int, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    ariadne_app = Ariadne.current()
    if not (
        group := asyncio.run_coroutine_threadsafe(
            ariadne_app.get_group(group_id), loop
        ).result()
    ):
        return GeneralResponse(
            code=402, message=f"group {group_id} does not exist!"
        )
    group_config = asyncio.run_coroutine_threadsafe(
        group.getConfig(), loop
    ).result()
    return GeneralResponse(
        data={
            "name": group_config.name,
            "announcement": group_config.announcement,
            "confess_talk": group_config.confess_talk,
            "allow_member_invite": group_config.allow_member_invite,
            "auto_approve": group_config.auto_approve,
            "anonymous_chat": group_config.anonymous_chat,
        }
    )


@app.post("/group/send")
async def send_group_message(
    group_id: int, message: list, token: bool = Depends(certify_token)
):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    ariadne_app = Ariadne.current()
    message = parse_messagechain(message)
    if not (
        group := asyncio.run_coroutine_threadsafe(
            ariadne_app.get_group(group_id), loop
        ).result()
    ):
        return GeneralResponse(
            code=402, message=f"group {group_id} does not exist!"
        )
    if isinstance(message, MessageChain):
        asyncio.run_coroutine_threadsafe(
            ariadne_app.send_group_message(
                group,
                message
                # MessageChain(message)
                # MessageChain.from_persistent_string(message).as_sendable()
            ),
            loop,
        ).result()
        return GeneralResponse()
    else:
        return GeneralResponse(
            code=403, data=message, message="missing parameters!"
        )


@app.get("/group/setting/get")
async def get_group_setting(group_id: int, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    columns = {
        i: Setting.__dict__[i]
        for i in Setting.__dict__.keys()
        if isinstance(Setting.__dict__[i], InstrumentedAttribute)
    }
    column_names = sorted(columns.keys())
    return (
        GeneralResponse(data=result)
        if (
            result := await orm.fetchall(
                select(*([columns[name] for name in column_names])).where(
                    Setting.group_id == group_id
                )
            )
        )
        else GeneralResponse(
            code=402, message=f"group {group_id} does not exist!"
        )
    )


@app.get("/group/setting/modify")
async def modify_group_setting(
    group_id: int,
    column: str,
    value: Union[int, str],
    token: bool = Depends(certify_token),
):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    columns = {
        i: Setting.__dict__[i]
        for i in Setting.__dict__.keys()
        if isinstance(Setting.__dict__[i], InstrumentedAttribute)
    }
    if column not in columns:
        return GeneralResponse(
            code=403,
            message=f"invalid column name: {column}! valid columns: {', '.join(columns.keys())}",
        )
    if not await orm.fetchone(
        select(Setting).where(Setting.group_id == group_id)
    ):
        return GeneralResponse(
            code=402, message=f"group {group_id} does not exist!"
        )
    value = (
        value in ("True", "true")
        if value in ("True", "true", "False", "false")
        else value
    )

    if command_index[column].is_valid(value):
        try:
            await orm.insert_or_update(
                Setting, [Setting.group_id == group_id], {column: value}
            )
        except Exception as e:
            logger.exception("")
            return GeneralResponse(code=500, message=str(e))
        return GeneralResponse()
    else:
        valid_values = command_index[column].valid_values
        valid_values = [str(i) for i in valid_values]
        return GeneralResponse(
            code=405,
            message=f"invalid value for column {column}: {value}! "
            f"valid values for {column}: {', '.join(valid_values)}",
        )


@app.get("/friend/list")
async def get_friend_list(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    ariadne_app = Ariadne.current()
    return GeneralResponse(
        data={
            friend.id: {"nickname": friend.nickname, "remark": friend.remark}
            for friend in (
                asyncio.run_coroutine_threadsafe(
                    ariadne_app.get_friend_list(), loop
                ).result()
            )
        }
    )


@app.get("/friend/detail")
async def get_friend_detail(friend_id: int, token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    ariadne_app = Ariadne.current()
    if not (
        friend := asyncio.run_coroutine_threadsafe(
            ariadne_app.get_friend(friend_id), loop
        ).result()
    ):
        return GeneralResponse(
            code=402, message=f"friend {friend_id} does not exist!"
        )
    friend_profile = asyncio.run_coroutine_threadsafe(
        friend.getProfile(), loop
    ).result()
    return GeneralResponse(
        data={
            "nickname": friend_profile.nickname,
            "email": friend_profile.email,
            "age": friend_profile.age,
            "level": friend_profile.level,
            "sign": friend_profile.sign,
            "sex": friend_profile.sex,
        }
    )


@app.post("/friend/send")
async def send_friend_message(
    friend_id: int, message: list, token: bool = Depends(certify_token)
):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    ariadne_app = Ariadne.current()
    message = parse_messagechain(message)
    if not (
        friend := asyncio.run_coroutine_threadsafe(
            ariadne_app.get_friend(friend_id), loop
        ).result()
    ):
        return GeneralResponse(
            code=402, message=f"friend {friend_id} does not exist!"
        )
    if isinstance(message, MessageChain):
        asyncio.run_coroutine_threadsafe(
            ariadne_app.send_friend_message(friend, message), loop
        ).result()
        return GeneralResponse()
    else:
        return GeneralResponse(
            code=403, data=message, message="missing parameters!"
        )


@app.get("/sys/info")
async def get_sys_info(token: bool = Depends(certify_token)):
    if not token:
        return GeneralResponse(code=401, message="invalid token!")
    mem = psutil.virtual_memory()
    return GeneralResponse(
        data={
            "memory": {"total": mem.total, "used": mem.used, "free": mem.free},
            "cpu": {
                "percent": psutil.cpu_percent(),
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq(),
            },
        }
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
