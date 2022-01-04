import re
import random
import base64
import aiohttp
import hashlib
import traceback
from loguru import logger
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import AccountMuted
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage


from sagiri_bot.orm.async_orm import orm
from sagiri_bot.core.app_core import AppCore
from sagiri_bot.orm.async_orm import KeywordReply
from sagiri_bot.decorators import switch, blacklist
from sagiri_bot.utils import user_permission_require
from sagiri_bot.handler.handler import AbstractHandler
from sagiri_bot.message_sender.message_item import MessageItem
from sagiri_bot.message_sender.message_sender import MessageSender
from sagiri_bot.message_sender.strategy import Normal, QuoteSource

saya = Saya.current()
channel = Channel.current()

channel.name("KeywordRespondent")
channel.author("SAGIRI-kawaii")
channel.description(
    "一个关键字回复插件，在群中发送已添加关键词可自动回复\n"
    "在群中发送 `添加回复关键词#{keyword}#{reply} 可添加关键词`\n"
    "在群中发送 `删除回复关键词#{keyword} 可删除关键词`"
)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def keyword_respondent(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if result := await KeywordRespondent.handle(app, message, group, member):
        await MessageSender(result.strategy).send(app, result.message, message, group, member)


class KeywordRespondent(AbstractHandler):
    __name__ = "KeywordRespondent"
    __description__ = "一个关键字回复插件"
    __usage__ = "在群中发送已添加关键词可自动回复\n" \
                "在群中发送 `添加回复关键词#{keyword}#{reply} 可添加关键词`\n" \
                "在群中发送 `删除回复关键词#{keyword} 可删除关键词`"

    @staticmethod
    @switch()
    @blacklist()
    async def handle(app: Ariadne, message: MessageChain, group: Group, member: Member):
        message_serialization = message.asPersistentString()
        if re.match(r"添加回复关键词#[\s\S]*#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                return await KeywordRespondent.update_keyword(message, message_serialization)
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource())
        elif re.match(r"删除回复关键词#[\s\S]*", message_serialization):
            if await user_permission_require(group, member, 2):
                return await KeywordRespondent.delete_keyword(app, message_serialization, group, member)
            else:
                return MessageItem(MessageChain.create([Plain(text="权限不足，爬")]), QuoteSource())
        elif result := await KeywordRespondent.keyword_detect(message_serialization):
            return result
        else:
            return None

    @staticmethod
    async def keyword_detect(keyword: str):
        if re.match(r"\[mirai:Image:{\"imageId\": \"{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:Image:{\"imageId\": \"{(.*)}\..*]", keyword, re.S)[0]
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
                    Plain(text=reply) if reply_type == "text" else Image(data_bytes=base64.b64decode(reply))
                ]),
                Normal()
            )
        else:
            return None

    @staticmethod
    async def update_keyword(message: MessageChain, message_serialization: str) -> MessageItem:
        _, keyword, reply = message_serialization.split("#")
        keyword = keyword.strip()
        keyword_type = "text"
        reply_type = "text"
        if re.match(r"\[mirai:Image:{\"imageId\": \"{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:Image:{\"imageId\": \"{(.*)}\..*]", keyword, re.S)[0]
            keyword_type = "img"

        if re.match(r"\[mirai:Image:{\"imageId\": \"{.*}\..*]", reply):
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
                return MessageItem(MessageChain.create([Plain(text=f"重复添加关键词！进程退出")]), Normal())
            else:
                await orm.add(
                    KeywordReply,
                    {"keyword": keyword, "reply": reply, "reply_type": reply_type, "reply_md5": reply_md5}
                )
                return MessageItem(MessageChain.create([Plain(text=f"关键词添加成功！")]), Normal())
        except:
            logger.error(traceback.format_exc())
            return MessageItem(MessageChain.create([Plain(text="发生错误！请查看日志！")]), Normal())

    @staticmethod
    async def delete_keyword(app: Ariadne, message_serialization: str, group: Group, member: Member):
        try:
            _, keyword = message_serialization.split("#")
        except ValueError:
            return MessageItem(
                MessageChain.create([
                    Plain(text="设置格式：\n添加关键词#关键词/图片#回复文本/图片\n"),
                    Plain(text="注：目前不支持文本中含有#！")
                ]),
                QuoteSource()
            )
        keyword = keyword.strip()
        if re.match(r"\[mirai:Image:{\"imageId\": \"{.*}\..*]", keyword):
            keyword = re.findall(r"\[mirai:Image:{\"imageId\": \"{(.*)}\..*]", keyword, re.S)[0]

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
                msg.append(Plain(text=replies[i][1]) if replies[i][0] == "text" else Image(data_bytes=base64.b64decode(replies[i][1])))
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
                return MessageItem(MessageChain.create([Plain(text="非预期回复，进程退出")]), Normal())
            elif 1 <= number <= len(replies):
                try:
                    await app.sendGroupMessage(
                        group,
                        MessageChain.create([
                            Plain(text="你确定要删除下列回复吗(是/否)：\n"),
                            Plain(text=keyword),
                            Plain(text="\n->\n"),
                            Plain(text=replies[number - 1][1]) if replies[number - 1][0] == "text" else Image(data_bytes=base64.b64decode(replies[number - 1][1]))
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
                return MessageItem(MessageChain.create([Plain(text="非预期回复，进程退出")]), Normal())
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
                    return MessageItem(MessageChain.create([Plain(text=f"删除成功")]), Normal())
                except Exception as e:
                    logger.error(traceback.format_exc())
                    return MessageItem(MessageChain.create([Plain(text=str(e))]), Normal())
            else:
                return MessageItem(MessageChain.create([Plain(text="进程退出")]), Normal())

        else:
            return MessageItem(MessageChain.create([Plain(text="未检测到此关键词数据！")]), QuoteSource())
