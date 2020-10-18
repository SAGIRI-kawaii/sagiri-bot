import datetime
import os

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import Image


from functions.basics.get_config import get_config
from functions.data_manage.get_data.get_total_calls import get_total_calls
from functions.data_manage.update_data.update_total_calls import update_total_calls
from functions.data_manage.get_data.get_user_clock_wallpaper_selected import get_user_clock_wallpaper_selected


async def get_wallpaper_time(group_id: int, sender: int) -> list:
    """
    Return time with wallpaper

    Args:
        group_id: Group id
        sender: Sender

    Examples:
        message = await get_wallpaper_time(group_id, sender)

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    clock_called = await get_total_calls("clock") + 1
    await update_total_calls(clock_called, "clock")
    if await get_user_clock_wallpaper_selected(group_id, sender) is None:
        msg_list = [
            At(target=sender),
            Plain(text="你还没有选择表盘哦~快来选择一个吧~\n"),
            Plain(text="看中后直接发送选择表盘+序号即可哦~\n"),
            Plain(text="如:选择表盘1\n"),
            Plain(text="表盘预览:")
        ]
        clock_wallpaper_preview_path = await get_config("clockWallpaperPreviewPath")
        wallpaper_list = os.listdir(clock_wallpaper_preview_path)
        wallpaper_list.sort(key=lambda x: int(x[:-4]))
        index = 1
        for i in wallpaper_list:
            msg_list.append(Plain(text="\n%s." % index))
            msg_list.append(Image.fromLocalFile(clock_wallpaper_preview_path+i))
            index += 1
        return [
            "None",
            MessageChain.create(msg_list)
        ]
    else:
        t = datetime.datetime.now()
        t = t.strftime("%H:%M")
        t = t.replace(":", "")
        path_list = [
            await get_config("clockWallpaperSavedPath"),
            str(await get_user_clock_wallpaper_selected(group_id, sender)),
            "\\%s.png" % t
        ]
        path = "".join(path_list)
        return [
            "None",
            MessageChain.create([
                Image.fromLocalFile(path)
            ])
        ]
