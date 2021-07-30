import re
import random
import base64
import aiohttp
import hashlib
import traceback
from loguru import logger
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.application.exceptions import AccountMuted
from graia.broadcast.interrupt import InterruptControl
from graia.application.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Plain, Image
from graia.application.event.messages import Group, Member, GroupMessage


from SAGIRIBOT.ORM.AsyncORM import orm
from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.ORM.AsyncORM import KeywordReply
from SAGIRIBOT.decorators import switch, blacklist
from SAGIRIBOT.utils import user_permission_require
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.MessageSender import GroupMessageSender
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, Normal, QuoteSource

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def keyword_reply_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if result := await KeywordReplyHandler.handle(app, message, group, member):
        await GroupMessageSender(result.strategy).send(app, result.message, message, group, member)


class KeywordReplyHandler(AbstractHandler):
    __name__ = "KeywordReplyHandler"
    __description__ = "一个关键字回复Handler"
    __usage__ = ""

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        message_serialization = message.asSerializationString().replace(
            "[mirai:source:" + re.findall(r'\[mirai:source:(.*?)]', message.asSerializationString(), re.S)[0] + "]", "")
        if re.match(r"添加回复关键词#[\s\S]*#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                return await KeywordReplyHandler.update_keyword(message, message_serialization)
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource(GroupStrategy()))
        elif re.match(r"删除回复关键词#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                return await KeywordReplyHandler.delete_keyword(app, message_serialization, group, member)
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource(GroupStrategy()))
        elif result := await KeywordReplyHandler.keyword_detect(message_serialization):
            return result
        else:
            return None

    @staticmethod
    async def keyword_detect(keyword: str):
        if re.match(r"\[mirai:image:{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
        if result := list(await orm.fetchall(
                select(
                    KeywordReply.reply, KeywordReply.reply_type
                ).where(
                    KeywordReply.keyword == keyword
                )
        )):
            reply, reply_type = random.choice(result)
            return MessageItem(
                MessageChain.create([
                    Plain(text=reply) if reply_type == "text" else Image.fromUnsafeBytes(base64.b64decode(reply))
                ]),
                Normal(GroupStrategy())
            )
        else:
            return None

    @staticmethod
    async def update_keyword(message: MessageChain, message_serialization: str) -> MessageItem:
        _, keyword, reply = message_serialization.split("#")
        keyword_type = "text"
        reply_type = "text"

        if re.match(r"\[mirai:image:{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]
            keyword_type = "img"

        if re.match(r"\[mirai:image:{.*}\..*]", reply):
            reply_type = "img"
            image: Image = message[Image][0] if keyword_type == "text" else message[Image][1]
            async with aiohttp.ClientSession() as session:
                async with session.get(url=image.url) as resp:
                    content = await resp.read()
            reply = base64.b64encode(content)
        else:
            reply = reply.encode("utf-8")

        m = hashlib.md5()
        m.update(reply)
        reply_md5 = m.hexdigest()

        try:
            if result := await orm.fetchone(select(KeywordReply).where(KeywordReply.keyword == keyword, KeywordReply.reply_type == reply_type, KeywordReply.reply_md5 == reply_md5)):
                print(result)
                return MessageItem(MessageChain.create([Plain(text=f"重复添加关键词！进程退出")]), Normal(GroupStrategy()))
            else:
                await orm.add(
                    KeywordReply,
                    {"keyword": keyword, "reply": reply, "reply_type": reply_type, "reply_md5": reply_md5}
                )
                return MessageItem(MessageChain.create([Plain(text=f"关键词添加成功！")]), Normal(GroupStrategy()))
        except Exception:
            logger.error(traceback.format_exc())
            return MessageItem(MessageChain.create([Plain(text="发生错误！请查看日志！")]), Normal(GroupStrategy()))

    @staticmethod
    async def delete_keyword(app: GraiaMiraiApplication, message_serialization: str, group: Group, member: Member):
        try:
            _, keyword = message_serialization.split("#")
        except ValueError:
            return MessageItem(
                MessageChain.create([
                    Plain(text="设置格式：\n添加关键词#关键词/图片#回复文本/图片\n"),
                    Plain(text="注：目前不支持文本中含有#！")
                ]),
                QuoteSource(GroupStrategy())
            )
        keyword = keyword.strip()
        if re.match(r"\[mirai:image:{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:image:{(.*?)}\..*]", keyword, re.S)[0]

        if results := await orm.fetchall(
            select(
                KeywordReply.reply_type, KeywordReply.reply, KeywordReply.reply_md5
            ).where(
                KeywordReply.keyword == keyword
            )
        ):
            replies = list()
            for result in results:
                content_type = result[0]
                content = result[1]
                content_md5 = result[2]
                replies.append([content_type, content, content_md5])

            msg = [Plain(text=f"关键词{keyword}目前有以下数据：\n")]
            for i in range(len(replies)):
                msg.append(Plain(text=f"{i + 1}. "))
                msg.append(Plain(text=replies[i][1]) if replies[i][0] == "text" else Image.fromUnsafeBytes(base64.b64decode(replies[i][1])))
                msg.append(Plain(text="\n"))
            msg.append(Plain(text="请发送你要删除的回复编号"))
            try:
                await app.sendGroupMessage(group, MessageChain.create(msg))
            except AccountMuted:
                return None

            inc = InterruptControl(AppCore.get_core_instance().get_bcc())

            @Waiter.create_using_function([GroupMessage])
            def number_waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
                if all([
                    waiter_group.id == group.id,
                    waiter_member.id == member.id,
                    waiter_message.asDisplay().isnumeric() and 0 < int(waiter_message.asDisplay()) <= len(replies)
                ]):
                    return int(waiter_message.asDisplay())
                elif all([
                    waiter_group.id == group.id,
                    waiter_member.id == member.id
                ]):
                    return -1

            number = await inc.wait(number_waiter)
            if number == -1:
                return MessageItem(MessageChain.create([Plain(text="非预期回复，进程退出")]), Normal(GroupStrategy()))
            elif 1 <= number <= len(replies):
                try:
                    await app.sendGroupMessage(
                        group,
                        MessageChain.create([
                            Plain(text="你确定要删除下列回复吗(是/否)：\n"),
                            Plain(text=keyword),
                            Plain(text="\n->\n"),
                            Plain(text=replies[number - 1][1]) if replies[number - 1][0] == "text" else Image.fromUnsafeBytes(base64.b64decode(replies[number - 1][1]))
                        ])
                    )
                except AccountMuted:
                    return None

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
                try:
                    await orm.delete(
                        KeywordReply,
                        [
                            KeywordReply.keyword == keyword,
                            KeywordReply.reply_md5 == replies[number - 1][2],
                            KeywordReply.reply_type == replies[number - 1][0]
                        ]
                    )
                    return MessageItem(MessageChain.create([Plain(text=f"删除成功")]), Normal(GroupStrategy()))
                except Exception as e:
                    logger.error(traceback.format_exc())
                    return MessageItem(MessageChain.create([Plain(text=str(e))]), Normal(GroupStrategy()))
            else:
                return MessageItem(MessageChain.create([Plain(text="进程退出")]), Normal(GroupStrategy()))

        else:
            return MessageItem(MessageChain.create([Plain(text="未检测到此关键词数据！")]), QuoteSource(GroupStrategy()))
