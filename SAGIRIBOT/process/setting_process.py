from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.data_manage.get_data.get_admin import get_admin
from SAGIRIBOT.data_manage.update_data.update_setting import update_setting

setting_value = {"Disable": False, "Enable": True, "on": True, "off": False, "Local": True, "Net": False,
                 "normal": "normal", "zuanLow": "zuanLow", "zuanHigh": "zuanHigh", "rainbow": "rainbow",
                 "chat": "chat", "online": "online", "offline": "offline", "wyy": "wyy", "qq": "qq",
                 "flashImage": "flashImage", "revoke": "revoke", "img": "img", "text": "text"}


async def judge_setting_legitimacy(config: str, new_value: str) -> bool:
    """
    Judge the setting value legitimacy

    Args:
        config: Setting name
        new_value: New setting value

    Examples:
        judge = await judge_setting_legitimacy(config, new_value)

    Return:
         bool
    """
    setting_torf = [
        "repeat", "countLimit", "tribute", "listen", "setu", "real", "bizhi", "search", "r18", "imgPredict",
        "imgLightning", "yellowPredict"
    ]
    setting_torf = set(setting_torf)
    if (config == "limit" or config == "tributeQuantity") and new_value.isnumeric():
        return True

    if new_value not in setting_value:
        return False
    new_value = setting_value[new_value]

    if config in setting_torf and (new_value is True or new_value is False):
        return True
    elif config == "music" and (new_value == "wyy" or new_value == "qq" or new_value == "off"):
        return True
    elif config == "speakMode" and (
            new_value == "normal" or new_value == "zuanHigh" or new_value == "zuanLow" or new_value == "rainbow" or new_value == "chat"):
        return True
    elif config == "switch" and (new_value == "online" or new_value == "offline"):
        return True
    elif config == "r18Process" and (new_value == "flashImage" or new_value == "revoke"):
        return True
    elif config == "longTextType" and (new_value == "text" or new_value == "img"):
        return True
    return False


async def setting_process(group_id: int, sender: int, config: str, new_value: str) -> list:
    """
    Process change setting requests

    Args:
        group_id: Group id
        sender: Sender
        config: Setting name
        new_value: New setting value

    Examples:
        message = await setting_process(group_id, sender, config, new_value)

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    admins = await get_admin(group_id)
    if sender not in admins:
        return [
            "None",
            MessageChain.create([
                Plain(text="You don't have the permission!")
            ])
        ]
    else:
        if await judge_setting_legitimacy(config, new_value):
            await update_setting(group_id, config, setting_value[new_value])
            return [
                "None",
                MessageChain.create([
                    Plain(text=f"config: {config} change to {new_value}")
                ])
            ]

        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="参数错误！请检查语句！")
                ])
            ]
