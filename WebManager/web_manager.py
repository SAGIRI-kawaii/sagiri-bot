from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.ORM.Tables import Setting
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.command_parse.Commands import *

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
    group_list = await AppCore.get_core_instance().get_app().groupList()
    return [{"value": group.id, "label": group.name} for group in group_list]


@app.get('/getGroupSetting')
async def getGroupSetting(groupId: int):
    options_bool = ["repeat", "countLimit", "setu", "bizhi", "real", "r18", "search", "yellowPredict", "searchBangumi",
               "debug", "compile", "antiRevoke", "achievement", "onlineNotice"]
    options_str = ["longTextType", "r18Process", "speakMode", "music", "switch"]
    valid_str_option_value = {
        "longTextType": ["text", "img"],
        "r18Process": ["revoke", "flashImage"],
        "speakMode": ["normal", "zuanLow", "zuanHigh", "rainbow", "chat"],
        "music": ["off", "wyy"],
        "switch": ["online", "offline"]
    }
    sql = f"SELECT `repeat`,countLimit,setu,bizhi,`real`,r18,search,yellowPredict,searchBangumi,debug,compile," \
          f"antiRevoke,achievement,onlineNotice FROM setting WHERE groupId={groupId} "
    bool_result = await execute_sql(sql)
    sql = f"SELECT longTextType,r18Process,speakMode,music,switch FROM setting WHERE groupId={groupId} "
    str_result = await execute_sql(sql)
    return [
        [{"label": options_bool[i], "value": True if bool_result[0][i] == 1 else False} for i in range(len(bool_result[0] if bool_result else 0))],
        [{"label": options_str[i], "value": str_result[0][i], "validValue": valid_str_option_value[options_str[i]]} for i in range(len(str_result[0] if str_result else 0))]
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


def run_api():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
