import re
import os
import random
import traceback
from typing import List
from loguru import logger
from datetime import datetime
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.element import Plain, Image, FlashImage, Forward, ForwardNode

from sagiri_bot.orm.async_orm import orm
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.strategy import Strategy
from sagiri_bot.utils import update_user_call_count_plus
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.utils import get_setting, user_permission_require
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import QuoteSource, Normal, Revoke
from sagiri_bot.orm.async_orm import TriggerKeyword, Setting, UserCalledCount
from sagiri_bot.decorators import frequency_limit_require_weight_free, switch, blacklist

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

core = AppCore.get_core_instance()
config = core.get_config()
bcc = core.get_bcc()


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
async def image_sender(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await ImageSender.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class ImageSender(AbstractHandler):
    __name__ = "ImageSender"
    __description__ = "一个可以发送图片的插件"
    __usage__ = "在群中发送设置好的关键词即可"
    paths = config.image_path
    functions = paths.keys()

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        if re.match(r"[\w]+ -[0-9]+", message.asPersistentString(), re.S):
            message_serialization = message.asPersistentString().split(" -")[0]
            image_count = int(message.asPersistentString().split(" -")[1])
        else:
            message_serialization = message.asPersistentString()
            image_count = 1

        if re.match(r"添加图库关键词#[\s\S]*#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                return await ImageSender.update_keyword(message_serialization)
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource())

        elif re.match(r"删除图库关键词#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                return await ImageSender.delete_keyword(app, group, member, message_serialization)
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource())

        elif re.match(r"查看图库关键词#[\s\S]*", message_serialization):
            return await ImageSender.show_keywords(message.asDisplay()[8:].strip())

        elif message.asDisplay().strip() == "查看已加载图库":
            return ImageSender.show_functions()

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
                if function in ImageSender.functions:
                    tfunc = function
                    break
            if not tfunc:
                return None
            else:
                if tfunc in user_called_column_index and tfunc in user_called_name_index:
                    await update_user_call_count_plus(
                        group,
                        member,
                        user_called_column_index[tfunc],
                        user_called_name_index[tfunc],
                        image_count
                    )
                if tfunc == "setu":
                    if await get_setting(group.id, Setting.setu):
                        if await get_setting(group.id, Setting.r18):
                            return await ImageSender.get_image_message(app, group, member, "setu18", image_count)
                        else:
                            return await ImageSender.get_image_message(app, group, member, tfunc, image_count)
                    else:
                        return MessageItem(MessageChain.create([Plain(text="这是正规群哦~没有那种东西的呢！lsp爬！")]), Normal())
                elif tfunc == "real_highq":
                    if await get_setting(group.id, Setting.real) and await get_setting(group.id, Setting.real_high_quality):
                        return await ImageSender.get_image_message(app, group, member, tfunc, image_count)
                    else:
                        return MessageItem(MessageChain.create([Plain(text="这是正规群哦~没有那种东西的呢！lsp爬！")]), Normal())
                else:
                    if tfunc not in setting_column_index or await get_setting(group.id, setting_column_index[tfunc]):
                        return await ImageSender.get_image_message(app, group, member, tfunc, image_count)
                    else:
                        return MessageItem(MessageChain.create([Plain(text="这是正规群哦~没有那种东西的呢！lsp爬！")]), Normal())
        else:
            return None

    @staticmethod
    def random_pic(base_path: str) -> str:
        path_dir = os.listdir(base_path)
        path = random.sample(path_dir, 1)[0]
        return base_path + path

    @staticmethod
    def get_pic(image_type: str, image_count: int) -> List[Image]:
        if image_type in ImageSender.functions:
            if not os.path.exists(ImageSender.paths[image_type]):
                return [Image(path=f"{os.getcwd()}/statics/error/path_not_exists.png")]
            else:
                return [Image(path=ImageSender.random_pic(ImageSender.paths[image_type])) for _ in range(image_count)]
        else:
            raise ValueError(f"Invalid image_type: {image_type}")

    @staticmethod
    async def get_message_item(app: Ariadne, group: Group, images: List[Image], image_count: int, strategy: Strategy):
        if image_count == 1:
            return MessageItem(
                message=MessageChain.create([images[0]]),
                strategy=strategy
            )
        else:
            # sender_name = (await app.getMember(group, config.bot_qq)).name
            node_list = [
                ForwardNode(
                    senderId=config.bot_qq,
                    time=datetime.now(),
                    senderName="SAGIRI BOT",
                    messageChain=MessageChain.create([image]),
                ) for image in images
            ]
            return MessageItem(
                message=MessageChain.create([Forward(node_list)]),
                strategy=strategy
            )

    @staticmethod
    @frequency_limit_require_weight_free(3)
    async def get_image_message(app: Ariadne, group: Group, member: Member, func: str, image_count: int) -> MessageItem:
        if image_count > 10:
            return MessageItem(MessageChain.create([Plain(text="要那么多？快爬！")]), QuoteSource())
        if image_count == 0:
            return MessageItem(MessageChain.create([Plain(text="0张要个头啊你，爪巴！")]), QuoteSource())
        if func == "setu18":
            r18_process = await get_setting(group.id, Setting.r18_process)
            if r18_process == "revoke":
                return await ImageSender.get_message_item(
                    app, group, ImageSender.get_pic(func, image_count), image_count, Revoke()
                )
            elif r18_process == "flashImage":
                return await ImageSender.get_message_item(
                    app=app,
                    group=group,
                    images=[FlashImage.fromImage(image) for image in ImageSender.get_pic(func, image_count)],
                    image_count=image_count,
                    strategy=Normal()
                )
            elif r18_process == "noProcess":
                return await ImageSender.get_message_item(
                    app, group, ImageSender.get_pic(func, image_count), image_count, Normal()
                )
            else:
                return await ImageSender.get_message_item(
                    app, group, ImageSender.get_pic(func, image_count), image_count, Normal()
                )
        return await ImageSender.get_message_item(
            app, group, ImageSender.get_pic(func, image_count), image_count, Normal()
        )

    @staticmethod
    async def update_keyword(message_serialization: str) -> MessageItem:
        _, function, keyword = message_serialization.split("#")
        if re.match(r"\[mirai:image:{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
        if function not in ImageSender.functions:
            return MessageItem(MessageChain.create([Plain(text="非法方法名！")]), QuoteSource())
        if await orm.fetchone(select(TriggerKeyword.keyword).where(TriggerKeyword.keyword == keyword)):
            return MessageItem(
                MessageChain.create([Plain(text="已存在的关键词！请先删除！")]),
                QuoteSource()
            )
        try:
            await orm.insert_or_ignore(
                TriggerKeyword,
                [TriggerKeyword.keyword == keyword, TriggerKeyword.function == function],
                {"keyword": keyword, "function": function}
            )
            return MessageItem(MessageChain.create([Plain(text=f"关键词添加成功！\n{keyword} -> {function}")]),
                               QuoteSource())
        except:
            logger.error(traceback.format_exc())
            return MessageItem(MessageChain.create([Plain(text="发生错误！请查看日志！")]), QuoteSource())

    @staticmethod
    async def delete_keyword(app: Ariadne, group: Group, member: Member, message_serialization: str) -> MessageItem:
        _, keyword = message_serialization.split("#")
        if re.match(r"\[mirai:image:{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
        if record := await orm.fetchone(select(TriggerKeyword.function).where(TriggerKeyword.keyword == keyword)):
            await app.sendGroupMessage(
                group,
                MessageChain.create([
                    Plain(text=f"查找到以下信息：\n{keyword} -> {record[0]}\n是否删除？（是/否）")
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
                return MessageItem(MessageChain.create([Plain(text="非预期回复，进程退出")]), Normal())
            elif result == "是":
                try:
                    await orm.delete(TriggerKeyword, [TriggerKeyword.keyword == keyword])
                except:
                    logger.error(traceback.format_exc())
                    return MessageItem(MessageChain.create([Plain(text="发生错误！请查看日志！")]), QuoteSource())
                return MessageItem(MessageChain.create([Plain(text=f"关键词 {keyword} 删除成功")]), Normal())
            else:
                return MessageItem(MessageChain.create([Plain(text="进程退出")]), Normal())
        else:
            return MessageItem(MessageChain.create([Plain(text="未找到关键词数据！请检查输入！")]), QuoteSource())

    @staticmethod
    async def show_keywords(function: str) -> MessageItem:
        if keywords := await orm.fetchall(select(TriggerKeyword.function).where(TriggerKeyword.function == function)):
            return MessageItem(
                MessageChain.create([
                    Plain(text='\n'.join([keyword[0] for keyword in keywords]))
                ]),
                QuoteSource()
            )
        else:
            return MessageItem(
                MessageChain.create([Plain(text=f"未找到图库{function}对应关键词或图库名错误！")]),
                QuoteSource()
            )

    @staticmethod
    def show_functions():
        if functions := config.image_path.keys():
            return MessageItem(
                MessageChain.create([
                    Plain(text="当前已加载图库：\n"),
                    Plain(text='\n'.join([func for func in functions]))
                ]),
                QuoteSource()
            )
        else:
            return MessageItem(
                MessageChain.create([Plain(text="未检测到已加载图库！请检查配置！")]),
                QuoteSource()
            )
