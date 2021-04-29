import re
import os
import random
import traceback
from loguru import logger
from sqlalchemy import select

from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member, GroupMessage
from graia.application.message.elements.internal import Plain, Image, Source

from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import set_result
from SAGIRIBOT.decorators import frequency_limit_require_weight_free
from SAGIRIBOT.ORM.Tables import TriggerKeyword, Setting, UserCalledCount
from SAGIRIBOT.utils import get_config, get_setting, user_permission_require
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, QuoteSource, Normal

setting_column_index = {
    "setu": Setting.setu,
    "real": Setting.real,
    "realHighq": Setting.real_high_quality,
    "bizhi": Setting.bizhi,
    "sketch": Setting.setu
}

user_called_column_index = {
    "setu": UserCalledCount.setu,
    "real": UserCalledCount.real,
    "realHighq": UserCalledCount.real,
    "bizhi": UserCalledCount.bizhi,
    "sketch": UserCalledCount.setu
}

user_called_name_index = {
    "setu": "setu",
    "real": "real",
    "realHighq": "real",
    "bizhi": "bizhi",
    "sketch": "setu"
}


class ImageSenderHandler(AbstractHandler):
    __name__ = "ImageSenderHandler"
    __description__ = "一个可以发送图片的Handler"
    __usage__ = "在群中发送设置好的关键词即可"
    functions = ("setu", "real", "realHighq", "bizhi", "sketch")

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_serialization = message.asSerializationString().replace(
            "[mirai:source:" + re.findall(r'\[mirai:source:(.*?)]', message.asSerializationString(), re.S)[0] + "]", "")

        if re.match(r"添加功能关键词#[\s\S]*#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                set_result(message, await self.update_keyword(message_serialization))
            else:
                set_result(message, MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource(GroupStrategy())))

        elif re.match(r"删除功能关键词#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                set_result(message, await self.delete_keyword(app, group, member, message_serialization))
            else:
                set_result(message, MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource(GroupStrategy())))

        if re.match(r"\[mirai:image:{.*}\..*]", message_serialization):
            message_serialization = re.findall(r"\[mirai:image:{(.*?)}\..*]", message_serialization, re.S)[0]

        if resp_functions := list(orm.fetchall(select(TriggerKeyword.function).where(TriggerKeyword.keyword == message_serialization))):
            resp_functions = resp_functions[0]
            tfunc = None
            for function in resp_functions:
                if function in self.functions:
                    tfunc = function
                    break
            if not tfunc:
                return None
            else:
                await update_user_call_count_plus1(group, member, user_called_column_index[tfunc], user_called_name_index[tfunc])
                if tfunc == "setu":
                    if await get_setting(group.id, Setting.setu):
                        if await get_setting(group.id, Setting.r18):
                            set_result(message, await self.get_image_message(group, member, "setu18"))
                        else:
                            set_result(message, await self.get_image_message(group, member, tfunc))
                    else:
                        set_result(message, MessageItem(MessageChain.create([Plain(text="这是正规群哦~没有那种东西的呢！lsp爬！")]), Normal(GroupStrategy())))
                elif tfunc == "realHighq":
                    if await get_setting(group.id, Setting.real) and await get_setting(group.id, Setting.real_high_quality):
                        set_result(message, await self.get_image_message(group, member, tfunc))
                    else:
                        set_result(message, MessageItem(MessageChain.create([Plain(text="这是正规群哦~没有那种东西的呢！lsp爬！")]), Normal(GroupStrategy())))
                else:
                    if await get_setting(group.id, setting_column_index[tfunc]):
                        set_result(message, await self.get_image_message(group, member, tfunc))
                    else:
                        set_result(message, MessageItem(MessageChain.create([Plain(text="这是正规群哦~没有那种东西的呢！lsp爬！")]), Normal(GroupStrategy())))
        else:
            return None

    @staticmethod
    def random_pic(base_path: str) -> str:
        path_dir = os.listdir(base_path)
        path = random.sample(path_dir, 1)[0]
        return base_path + path

    @staticmethod
    async def get_pic(image_type: str) -> Image:

        async def color() -> str:
            base_path = get_config("setuPath")
            return f"{os.getcwd()}/statics/error/path_not_exists.png" if not os.path.exists(base_path) else ImageSenderHandler.random_pic(base_path)

        async def color18() -> str:
            base_path = get_config("setu18Path")
            return f"{os.getcwd()}/statics/error/path_not_exists.png" if not os.path.exists(base_path) else ImageSenderHandler.random_pic(base_path)

        async def real() -> str:
            base_path = get_config("realPath")
            return f"{os.getcwd()}/statics/error/path_not_exists.png" if not os.path.exists(base_path) else ImageSenderHandler.random_pic(base_path)

        async def real_highq() -> str:
            base_path = get_config("realHighqPath")
            return f"{os.getcwd()}/statics/error/path_not_exists.png" if not os.path.exists(base_path) else ImageSenderHandler.random_pic(base_path)

        async def wallpaper() -> str:
            base_path = get_config("wallpaperPath")
            return f"{os.getcwd()}/statics/error/path_not_exists.png" if not os.path.exists(base_path) else ImageSenderHandler.random_pic(base_path)

        async def sketch() -> str:
            base_path = get_config("sketchPath")
            return f"{os.getcwd()}/statics/error/path_not_exists.png" if not os.path.exists(base_path) else ImageSenderHandler.random_pic(base_path)

        switch = {
            "setu": color,
            "setu18": color18,
            "real": real,
            "realHighq": real_highq,
            "bizhi": wallpaper,
            "sketch": sketch
        }

        target_pic_path = await switch[image_type]()
        return Image.fromLocalFile(target_pic_path)

    @staticmethod
    @frequency_limit_require_weight_free(3)
    async def get_image_message(group: Group, member: Member, func: str) -> MessageItem:
        return MessageItem(MessageChain.create([await ImageSenderHandler.get_pic(func)]), Normal(GroupStrategy()))

    @staticmethod
    async def update_keyword(message_serialization: str) -> MessageItem:
        _, function, keyword = message_serialization.split("#")
        if re.match(r"\[mirai:image:{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
        if function not in ImageSenderHandler.functions:
            return MessageItem(MessageChain.create([Plain(text="非法方法名！")]), QuoteSource(GroupStrategy()))
        try:
            orm.update(
                TriggerKeyword,
                {"keyword": keyword, "function": function},
                {"keyword": keyword, "function": function}
            )
            return MessageItem(MessageChain.create([Plain(text=f"关键词添加成功！\n{keyword} -> {function}")]),
                               QuoteSource(GroupStrategy()))
        except Exception:
            logger.error(traceback.format_exc())
            orm.session.rollback()
            return MessageItem(MessageChain.create([Plain(text="发生错误！请查看日志！")]), QuoteSource(GroupStrategy()))

    @staticmethod
    async def delete_keyword(app: GraiaMiraiApplication, group: Group, member: Member, message_serialization: str) -> MessageItem:
        _, keyword = message_serialization.split("#")
        if re.match(r"\[mirai:image:{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
        if record := list(orm.fetchone(select(TriggerKeyword.function).where(TriggerKeyword.keyword == keyword))):
            await app.sendGroupMessage(
                group,
                MessageChain.create([
                    Plain(text=f"查找到以下信息：\n{keyword} -> {record[0][0]}\n是否删除？（是/否）")
                ])
            )
            inc = InterruptControl(AppCore.get_core_instance().get_bcc())

            @Waiter.create_using_function([GroupMessage])
            def confirm_waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
                if all([
                    waiter_group.id == group.id,
                    waiter_member.id == member.id
                ]):
                    if re.match(r"[是否]", waiter_message.asDisplay()):
                        return waiter_message.asDisplay()
                    else:
                        return ""

            result = await inc.wait(confirm_waiter)

            if not result:
                return MessageItem(MessageChain.create([Plain(text="非预期回复，进程退出")]), Normal(GroupStrategy()))
            elif result == "是":
                orm.delete(TriggerKeyword, {"keyword": keyword})
                return MessageItem(MessageChain.create([Plain(text=f"关键词 {keyword} 删除成功")]), Normal(GroupStrategy()))
            else:
                return MessageItem(MessageChain.create([Plain(text="进程退出")]), Normal(GroupStrategy()))
        else:
            return MessageItem(MessageChain.create([Plain(text="未找到关键词数据！请检查输入！")]), QuoteSource(GroupStrategy()))
