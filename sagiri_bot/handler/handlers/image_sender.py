import re
import os
import random
import aiohttp
import traceback
from loguru import logger
from datetime import datetime
from sqlalchemy import select
from typing import Union, List

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.element import Plain, Image, FlashImage, Forward, ForwardNode, Source

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.config import GlobalConfig
from sagiri_bot.internal_utils import update_user_call_count_plus
from sagiri_bot.internal_utils import group_setting, user_permission_require
from sagiri_bot.orm.async_orm import TriggerKeyword, Setting, UserCalledCount

setting_column_index = {
    "setu": Setting.setu,
    "real": Setting.real,
    "real_highq": Setting.real_high_quality,
    "bizhi": Setting.bizhi,
    "sketch": Setting.setu
}

user_called_column_index = {
    "setu": UserCalledCount.setu,
    "real": UserCalledCount.real,
    "real_highq": UserCalledCount.real,
    "bizhi": UserCalledCount.bizhi,
    "sketch": UserCalledCount.setu
}

user_called_name_index = {
    "setu": "setu",
    "real": "real",
    "real_highq": "real",
    "bizhi": "bizhi",
    "sketch": "setu"
}
url_pattern = r"((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"

saya = Saya.current()
channel = Channel.current()

channel.name("ImageSender")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个可以发送图片的插件，在群中发送设置好的关键词即可\n"
    "发送 `添加图库关键词#{图库名（配置文件中路径key值）}#{keyword}即可进行关键词的添加\n"
    "发送 `删除图库关键词#{图库名（配置文件中路径key值）}即可进行关键词的删除\n"
    "发送 `查看图库关键词#{图库名（配置文件中路径key值）}即可进行关键词的查看`"
)

config = create(GlobalConfig)
bcc = saya.broadcast
paths = config.image_path
functions = paths.keys()


@bcc.receiver(ApplicationLaunched)
async def db_init():
    for key in config.image_path.keys():
        try:
            await orm.insert_or_ignore(
                TriggerKeyword,
                [TriggerKeyword.keyword == key, TriggerKeyword.function == key],
                {"keyword": key, "function": key}
            )
        except Exception:
            pass


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def image_sender(app: Ariadne, message: MessageChain, group: Group, member: Member, source: Source):
    if re.match(r"[\w]+ -[0-9]+", message.as_persistent_string(), re.S):
        message_serialization = message.as_persistent_string().split(" -")[0]
        image_count = int(message.as_persistent_string().split(" -")[1])
    else:
        message_serialization = message.as_persistent_string()
        image_count = 1

    if re.match(r"添加图库关键词#[\s\S]*#[\s\S]*", message_serialization):
        if await user_permission_require(group, member, 2):
            return await app.send_group_message(group, await update_keyword(message_serialization), quote=source)
        else:
            return await app.send_group_message(group, MessageChain("权限不足，爬"), quote=source)

    elif re.match(r"删除图库关键词#[\s\S]*", message_serialization):
        if await user_permission_require(group, member, 2):
            return await app.send_group_message(
                group,
                await delete_keyword(app, group, member, message_serialization),
                quote=source
            )
        else:
            return await app.send_group_message(group, MessageChain("权限不足，爬"), quote=source)

    elif re.match(r"查看图库关键词#[\s\S]*", message_serialization):
        return await app.send_group_message(
            group,
            await show_keywords(message.display[8:].strip()),
            quote=source
        )

    elif message.display.strip() == "查看已加载图库":
        return await app.send_group_message(group, show_functions(), quote=source)

    if re.match(r"\[mirai:image:{.*}\..*]", message_serialization):
        message_serialization = re.findall(r"\[mirai:image:{(.*?)}\..*]", message_serialization, re.S)[0]

    if resp_functions := list(
        await orm.fetchall(
            select(TriggerKeyword.function).where(TriggerKeyword.keyword == message_serialization)
        )
    ):
        resp_functions = resp_functions[0]
        tfunc = None
        for function in resp_functions:
            if function in functions:
                tfunc = function
                break
        if not tfunc:
            return
        else:
            if tfunc in user_called_column_index and tfunc in user_called_name_index:
                await update_user_call_count_plus(
                    group,
                    member,
                    user_called_column_index[tfunc],
                    user_called_name_index[tfunc],
                    image_count
                )
            if tfunc == "setu" or tfunc == "setu18":
                if await group_setting.get_setting(group.id, Setting.setu):
                    if await group_setting.get_setting(group.id, Setting.r18):
                        return await app.send_group_message(
                            group,
                            await get_image_message(group, "setu18", image_count),
                            quote=source
                        )
                    elif tfunc == "setu":
                        return await app.send_group_message(
                            group,
                            await get_image_message(group, tfunc, image_count),
                            quote=source
                        )
                    else:
                        return await app.send_group_message(group, MessageChain("这是正规群哦~没有那种东西的呢！lsp爬！"))
                else:
                    return await app.send_group_message(group, MessageChain("这是正规群哦~没有那种东西的呢！lsp爬！"))
            elif tfunc == "real_highq":
                if all([
                    await group_setting.get_setting(group.id, Setting.real),
                    await group_setting.get_setting(group.id, Setting.real_high_quality)
                ]):
                    return await app.send_group_message(
                        group,
                        await get_image_message(group, tfunc, image_count),
                        quote=source
                    )
                else:
                    return await app.send_group_message(group, MessageChain("这是正规群哦~没有那种东西的呢！lsp爬！"))
            else:
                if any([
                    tfunc not in setting_column_index,
                    await group_setting.get_setting(group.id, setting_column_index[tfunc])
                ]):
                    return await app.send_group_message(
                        group,
                        await get_image_message(group, tfunc, image_count),
                        quote=source
                    )
                else:
                    return await app.send_group_message(group, MessageChain("这是正规群哦~没有那种东西的呢！lsp爬！"))


def random_pic(base_path: str) -> str:
    path_dir = os.listdir(base_path)
    path = random.sample(path_dir, 1)[0]
    return base_path + path


async def get_pic(image_type: str, image_count: int) -> Union[List[Image], str]:
    if image_type not in functions:
        raise ValueError(f"Invalid image_type: {image_type}")
    if os.path.exists(paths[image_type]):
        return [Image(path=random_pic(paths[image_type])) for _ in range(image_count)]
    elif re.match(
        r"json:([\w\W]+\.)+([\w\W]+)\$" + url_pattern,
        paths[image_type]
    ):
        path = paths[image_type].split('$')[0].split(':')[1].split('.')
        result = []
        async with aiohttp.ClientSession() as session:
            for _ in range(image_count):
                async with session.get(paths[image_type].split('$')[-1]) as resp:
                    res = await resp.json()
                for p in path:
                    try:
                        if p[0] == '|' and p[1:].isnumeric():
                            res = res[int(p[1:])]
                        else:
                            res = res.get(p)
                    except TypeError:
                        logger.error("json解析失败！")
                        return "json解析失败！请查看配置路径是否正确或API是否有变动！"
                async with session.get(res) as resp:
                    result.append(Image(data_bytes=await resp.read()))
        return result
    elif re.match(url_pattern, paths[image_type]):
        result = []
        async with aiohttp.ClientSession() as session:
            for _ in range(image_count):
                async with session.get(paths[image_type]) as resp:
                    result.append(Image(data_bytes=await resp.read()))
        return result
    else:
        return [Image(path=f"{os.getcwd()}/statics/error/path_not_exists.png")]


async def get_message(images: Union[List[Image], str], image_count: int) -> MessageChain:
    if isinstance(images, str):
        return MessageChain(images)
    if image_count == 1:
        return MessageChain([images[0]])
    node_list = [
        ForwardNode(
            sender_id=config.bot_qq,
            time=datetime.now(),
            sender_name="SAGIRI BOT",
            message_chain=MessageChain([image]),
        ) for image in images
    ]
    return MessageChain([Forward(node_list)])


async def get_image_message(group: Group, func: str, image_count: int) -> MessageChain:
    if image_count > 10:
        return MessageChain("要那么多？快爬！")
    if image_count == 0:
        return MessageChain("0张要个头啊你，爪巴！")
    if func == "setu18":
        r18_process = await group_setting.get_setting(group.id, Setting.r18_process)
        if (
            r18_process == "revoke"
            or r18_process != "flashImage"
            and r18_process == "noProcess"
            or r18_process != "flashImage"
        ):
            return await get_message(await get_pic(func, image_count), image_count)
        else:
            return await get_message(
                [FlashImage.from_image(image) for image in await get_pic(func, image_count)],
                image_count
            )
    return await get_message(
        await get_pic(func, image_count), image_count
    )


async def update_keyword(message_serialization: str) -> MessageChain:
    _, function, keyword = message_serialization.split("#")
    if re.match(r"\[mirai:image:{.*}\..*]", keyword):
        keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
    if function not in functions:
        return MessageChain("非法方法名！")
    if await orm.fetchone(select(TriggerKeyword.keyword).where(TriggerKeyword.keyword == keyword)):
        return MessageChain("已存在的关键词！请先删除！")
    try:
        await orm.insert_or_ignore(
            TriggerKeyword,
            [TriggerKeyword.keyword == keyword, TriggerKeyword.function == function],
            {"keyword": keyword, "function": function}
        )
        return MessageChain(f"关键词添加成功！\n{keyword} -> {function}")
    except:
        logger.error(traceback.format_exc())
        return MessageChain("发生错误！请查看日志！")


async def delete_keyword(app: Ariadne, group: Group, member: Member, message_serialization: str) -> MessageChain:
    _, keyword = message_serialization.split("#")
    if re.match(r"\[mirai:image:{.*}\..*]", keyword):
        keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
    if record := await orm.fetchone(select(TriggerKeyword.function).where(TriggerKeyword.keyword == keyword)):
        await app.send_group_message(
            group,
            MessageChain([
                Plain(text=f"查找到以下信息：\n{keyword} -> {record[0]}\n是否删除？（是/否）")
            ])
        )
        inc = InterruptControl(saya.broadcast)

        @Waiter.create_using_function([GroupMessage])
        def confirm_waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
            if all([
                waiter_group.id == group.id,
                waiter_member.id == member.id
            ]):
                if re.match(r"[是否]", waiter_message.display):
                    return waiter_message.display
                else:
                    return ""

        result = await inc.wait(confirm_waiter)

        if not result:
            return MessageChain("非预期回复，进程退出")
        elif result == "是":
            try:
                await orm.delete(TriggerKeyword, [TriggerKeyword.keyword == keyword])
            except:
                logger.error(traceback.format_exc())
                return MessageChain("发生错误！请查看日志！")
            return MessageChain(f"关键词 {keyword} 删除成功")
        else:
            return MessageChain("进程退出")
    else:
        return MessageChain("未找到关键词数据！请检查输入！")


async def show_keywords(function: str) -> MessageChain:
    if keywords := await orm.fetchall(select(TriggerKeyword.keyword).where(TriggerKeyword.function == function)):
        return MessageChain('\n'.join([keyword[0] for keyword in keywords]))
    else:
        return MessageChain(f"未找到图库{function}对应关键词或图库名错误！")


def show_functions() -> MessageChain:
    if loaded_functions := config.image_path.keys():
        return MessageChain([
            "当前已加载图库：\n",
            '\n'.join([func for func in loaded_functions])
        ])
    else:
        return MessageChain("未检测到已加载图库！请检查配置！")
