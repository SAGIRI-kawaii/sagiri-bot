import uvicorn
import datetime
from loguru import logger
from fastapi import FastAPI
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware

from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.command_parse.Commands import *
from SAGIRIBOT.ORM.Tables import Setting, FunctionCalledRecord

app = FastAPI(docs_url=None, redoc_url=None)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/getGroups')
async def getGroups():
    groups = orm.fetchall(select(Setting.group_id, Setting.group_name).where(Setting.active == True))
    return [{"value": group[0], "label": group[1]} for group in groups]


@app.get('/getGroupSetting')
async def getGroupSetting(groupId: int):
    options_bool = ["repeat", "frequency_limit", "setu", "real", "bizhi", "r18", "img_search", "bangumi_search",
               "debug", "compile", "anti_revoke", "online_notice", "switch"]
    options_str = ["long_text_type", "r18_process", "speak_mode", "music"]
    valid_str_option_value = {
        "long_text_type": LongTextType.valid_values,
        "r18_process": R18Process.valid_values,
        "speak_mode": SpeakMode.valid_values,
        "music": Music.valid_values
    }
    bool_result = list(orm.fetchone(select(
        Setting.repeat,
        Setting.frequency_limit,
        Setting.setu, Setting.real, Setting.bizhi, Setting.r18,
        Setting.img_search,
        Setting.bangumi_search,
        Setting.debug,
        Setting.compile,
        Setting.anti_revoke,
        Setting.online_notice,
        Setting.switch
    ).where(
        Setting.group_id == groupId
    )))[0]
    str_result = list(orm.fetchone(select(
        Setting.long_text_type,
        Setting.r18_process,
        Setting.speak_mode,
        Setting.music
    ).where(
        Setting.group_id == groupId
    )))[0]
    return [
        [{"label": options_bool[i], "value": bool_result[i]} for i in range(len(bool_result))],
        [{"label": options_str[i], "value": str_result[i], "validValue": valid_str_option_value[options_str[i]]} for i in range(len(str_result))]
    ]


@app.get('/modifyGroupSetting')
async def modifyGroupSetting(groupId: int, settingName: str, newValue):
    if newValue in ["true", "false"]:
        newValue = True if newValue == "true" else False
    try:
        orm.update(
            Setting,
            {"group_id": groupId},
            {"group_id": groupId, settingName: newValue}
        )
    except Exception as e:
        logger.error(f"api error: {e}")
        orm.rollback()
        return False
    return True


@app.get("/getStatus")
async def getStatus():
    return {
        "functionCalled": len(orm.fetchall(
            select(FunctionCalledRecord).where(FunctionCalledRecord.time > datetime.date.today())
        )),
        "handlerCount": len(AppCore.get_core_instance().get_group_chain()),
        "sayaCount": len(AppCore.get_core_instance().get_saya_channels())
    }


def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
