import os
import random
import string
import hashlib
from sqlalchemy import select
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from creart import create
from graia.saya import Saya
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.model.relationship import MemberPerm

from .models import *
from shared.orm import orm, APIAccount, ChatRecord

logs = []


def set_log(log_str: str):
    logs.append(log_str.strip())


def md5(content: str) -> str:
    return hashlib.md5(content.encode(encoding="utf-8")).hexdigest()


async def has_account(username: str) -> bool:
    return bool(await orm.fetchone(select(APIAccount.applicant).where(APIAccount.username == username)))


async def account_legal(username: str, password: str) -> bool:
    return bool(await orm.fetchone(
        select(APIAccount.applicant).where(APIAccount.username == username, APIAccount.password == password)
    ))


async def generate_account(applicant: id) -> User:
    username = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    _ = await orm.insert_or_update(
        APIAccount,
        [APIAccount.applicant == applicant],
        {"username": username, "password": md5(password), "applicant": applicant}
    )
    return User(username=username, password=password)


def get_all_channels() -> list[str]:
    ignore = ["__init__.py", "__pycache__"]
    dirs = [
        "modules/required",
        "modules/self_contained",
        "modules/third_party"
    ]
    modules = []
    for path in dirs:
        for module in os.listdir(path):
            if module in ignore:
                continue
            if os.path.isdir(module):
                modules.append(f"{path.replace('/', '.')}.{module}")
            else:
                modules.append(f"{path.replace('/', '.')}.{module.split('.')[0]}")
    return modules


def get_not_installed_channels() -> list[str]:
    installed_channels = create(Saya).channels.keys()
    all_channels = get_all_channels()
    return [channel for channel in all_channels if channel not in installed_channels]


def install_channel(channel: str) -> GeneralResponse:
    ignore = ["__init__.py", "__pycache__"]
    saya = create(Saya)
    with saya.module_context():
        if channel in ignore:
            return GeneralResponse(code=202, message=f"module {channel} in the ignore list")
        try:
            saya.require(channel)
        except Exception as e:
            return GeneralResponse(
                code=500,
                data={"error": e},
                message=f"Module {channel} installation error",
            )
    return GeneralResponse()


def uninstall_channel(channel: str) -> GeneralResponse:
    saya = create(Saya)
    if channel not in saya.channels:
        return GeneralResponse(code=402, message=f"module {channel} does not exist!")
    with saya.module_context():
        try:
            saya.uninstall_channel(saya.channels[channel])
        except Exception as e:
            return GeneralResponse(
                code=500,
                data={"error": e},
                message=f"Module {channel} uninstall error",
            )
    return GeneralResponse()


def reload_channel(channel: str) -> GeneralResponse:
    saya = create(Saya)
    if channel not in saya.channels:
        return GeneralResponse(code=402, message=f"module {channel} does not exist!")
    with saya.module_context():
        try:
            saya.reload_channel(saya.channels[channel])
        except Exception as e:
            return GeneralResponse(
                code=500,
                data={"error": e},
                message=f"Module {channel} reload error",
            )
    return GeneralResponse()


def parse_messagechain(message: list) -> MessageChain | list:
    """
    {
        type: str(Union[plain, image]),
        data: {
            content: Optional[Union[str, bytes]],
            url: Optional[str],
            path: Optional[str]
        }
    }
    """
    elements = []
    exceptions = []
    for element in message:
        if element["type"] == "plain":
            if content := element.get("content"):
                elements.append(Plain(content))
            else:
                exceptions.append((element, "missing parameter: content"))
        elif element["type"] == "image":
            if content := element.get("content"):
                elements.append(Image(data_bytes=content))
            elif base64 := element.get("base64"):
                elements.append(Image(base64=base64))
            elif url := element.get("url"):
                elements.append(Image(url=url))
            elif path := element.get("path"):
                elements.append(Image(path=path))
            else:
                exceptions.append((element, "missing parameter: content(bytes) / base64(str) / url(str) / path(str)"))
    return MessageChain(elements) if not exceptions else exceptions


def get_last_time(hour: int = 24) -> datetime:
    curr_time = datetime.now()
    return curr_time - timedelta(hours=hour)


async def get_talk_count_by_hour(hour: int = 8) -> list:
    data = await orm.fetchall(
        select(
            func.strftime("%H", ChatRecord.time), func.count(ChatRecord.id)
        ).where(
            ChatRecord.time >= get_last_time(hour),
        ).group_by(
            func.strftime("%H", ChatRecord.time)
        )
    )
    return [{"time": item[0], "count": item[1]} for item in data]


def max_permission(permissions: list[MemberPerm]) -> MemberPerm:
    permissions = set(permissions)
    if MemberPerm.Owner in permissions:
        return MemberPerm.Owner
    elif MemberPerm.Administrator in permissions:
        return MemberPerm.Administrator
    else:
        return MemberPerm.Member
