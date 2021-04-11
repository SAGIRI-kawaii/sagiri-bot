import re
import time
import string
import random
import aiohttp
import hashlib
import traceback
from urllib import parse
from loguru import logger

from sqlalchemy import select, desc
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import Group, Member
from graia.application.message.elements.internal import Plain, At

from SAGIRIBOT.utils import get_config
from SAGIRIBOT.ORM.ORM import orm
from SAGIRIBOT.Handler.Handler import AbstractHandler
from SAGIRIBOT.utils import update_user_call_count_plus1
from SAGIRIBOT.MessageSender.MessageItem import MessageItem
from SAGIRIBOT.MessageSender.Strategy import GroupStrategy, AtSender
from SAGIRIBOT.ORM.Tables import Setting, ChatSession, UserCalledCount


class ChatReplyHandler(AbstractHandler):
    __name__ = "ChatReplyHandler"
    __description__ = "一个可以自定义/。智能回复的Handler"
    __usage__ = "在群中发送 `@bot + 想说的话` 即可"

    async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
        if message.has(At) and message.get(At)[0].target == get_config("BotQQ"):
            await update_user_call_count_plus1(group, member, UserCalledCount.at, "at")
            content = "".join(plain.text for plain in message.get(Plain)).strip().replace(" ", "，")
            return await self.get_reply(member.id, group.id, content)
        else:
            return await super().handle(app, message, group, member)

    @staticmethod
    async def get_reply(member_id: int, group_id: int, content: str):
        if mode_now := list(orm.fetchone(select(Setting.speak_mode).where(Setting.group_id == group_id))):
            mode_now = mode_now[0][0]
            if mode_now == "normal":
                return None
            elif mode_now == "zuanLow":
                url = f"https://nmsl.shadiao.app/api.php?level=min&from={get_config('shadiaoAppName')}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url) as resp:
                        text = await resp.text()
            elif mode_now == "zuanHigh":
                url = f"https://nmsl.shadiao.app/api.php?from={get_config('shadiaoAppName')}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url) as resp:
                        text = await resp.text()
            elif mode_now == "rainbow":
                url = f"https://chp.shadiao.app/api.php?from={get_config('shadiaoAppName')}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url) as resp:
                        text = await resp.text()

            elif mode_now == "chat":
                text = await ChatReplyHandler.get_chat_reply(group_id, member_id, content)
            else:
                raise Exception(f"数据库群 <{group_id}> speak_mode项非法！目前值：{mode_now}")
            return MessageItem(MessageChain.create([Plain(text=text)]), AtSender(GroupStrategy()))
        else:
            raise Exception(f"数据库未查找到群 <{group_id}> speak_mode项，请检查数据库！")

    @staticmethod
    async def get_chat_reply(group_id: int, sender: int, text: str) -> str:
        if text.strip() == "":
            return "@纱雾干什么呐~是想找纱雾玩嘛~"
        url = "https://api.ai.qq.com/fcgi-bin/nlp/nlp_textchat"
        temp_list = re.findall(r"@(.*?) ", text, re.S)
        if temp_list:
            text = text.replace(f"@{temp_list[0]} ", "")
        text = text.strip()
        # print("question:", text)
        # print(text, temp_list)
        app_id = get_config("txAppId")
        t = time.time()
        time_stamp = str(int(t))
        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 10))

        params = {
            'app_id': app_id,
            'question': text,
            'time_stamp': time_stamp,
            'nonce_str': nonce_str,
            'session': await ChatReplyHandler.get_chat_session(group_id, sender)
        }
        sign = await ChatReplyHandler.get_tx_sign(params)
        params["sign"] = sign

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params) as resp:
                res = await resp.json()
        if res["ret"] == 16394:
            return "抱歉呐~我不知道怎么回答呢~问我点别的吧~"
        if res["ret"] > 0:
            print(res)
            return f"Error:{res['msg']}"
        return res["data"]["answer"]

    @staticmethod
    async def get_chat_session(group_id: int, member_id: int) -> str:
        if result := list(
            orm.fetchone(
                select(
                    ChatSession.member_session
                ).where(
                    ChatSession.group_id == group_id,
                    ChatSession.member_id == member_id
                )
            )
        ):
            return str(result[0][0])
        else:
            new_session = list(orm.fetchall(select(ChatSession.member_session).order_by(desc(ChatSession.member_session))))
            new_session = new_session[0][0] + 1 if new_session else 1
            logger.info(f"new_session for {group_id} -> {member_id}: {new_session}")
            try:
                orm.add(
                    ChatSession,
                    {
                        "group_id": group_id,
                        "member_id": member_id,
                        "member_session": new_session
                    }
                )
                return str(new_session)
            except Exception as e:
                logger.error(traceback.format_exc())
                orm.session.rollback()

    @staticmethod
    async def get_tx_sign(params: dict) -> str:
        """
        Get sign of Tencent Ai Platform

        Args:
            params: Dict to send

        Examples:
            sign = await get_sign(params)

        Return:
            str
        """
        app_key = get_config("txAppKey")
        params_keys = sorted(params.keys())
        sign = ""
        for i in params_keys:
            if params[i] != '':
                sign += "%s=%s&" % (i, parse.quote(params[i], safe=''))
        sign += "app_key=%s" % app_key

        def curl_md5(src: str) -> str:
            m = hashlib.md5(src.encode('UTF-8'))
            return m.hexdigest().upper()

        sign = curl_md5(sign)
        # print("signMD5:", sign)
        return sign
