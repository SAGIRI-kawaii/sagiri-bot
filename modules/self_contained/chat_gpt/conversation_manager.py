import re
import asyncio
import aiohttp
from loguru import logger
from typing import TypedDict
from chatgpt.api import ChatGPT
from chatgpt.exceptions import StatusCodeException, UnauthorizedException

from creart import create
from graia.ariadne.model.relationship import Group, Member

from core import Sagiri

config = create(Sagiri).config
proxy = config.proxy if config.proxy != "proxy" else None
configs = config.functions.get("chat_gpt")
email = configs.get("email")
password = configs.get("password")
cookie = configs.get("cookie")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 Edg/107.0.1418.62',
}
session_token: str = ""


async def create_gpt(response_timeout: int = 100, proxies: str | None = None):
    if not session_token:
        _ = await login()
    return ChatGPT(response_timeout=response_timeout, session_token=session_token, proxies=proxies)


async def login():
    logger.info("start getting openai token")
    global session_token
    async with aiohttp.ClientSession() as session:
        async with session.get("https://chat.openai.com/api/auth/csrf", headers=headers, proxy=proxy) as resp:
            csrf_token = (await resp.json())['csrfToken']
        logger.success(f"get csrf_token successfully: {csrf_token}")
        async with session.post(
                "https://chat.openai.com/api/auth/signin/auth0?prompt=login", headers=headers, proxy=proxy,
                data={'callbackUrl': '/', 'csrfToken': csrf_token, 'json': 'true'}) as resp:
            if resp.status != 200:
                raise ValueError(f'Status code {resp.status}: {await resp.text()}')
            redirect_url = (await resp.json())['url']
        logger.success(f"get redirect_url successfully: {redirect_url}")
        async with session.get(redirect_url, headers=headers, proxy=proxy) as resp:
            if resp.status != 200:
                raise ValueError(f'Status code {resp.status}: {await resp.text()}')
            pattern = r'<input type="hidden" name="state" value="(.*)" \/>'
            results = re.findall(pattern, await resp.text())
            if not results:
                raise ValueError(f'Could not get state: {await resp.text()}')
            state = results[0]
        logger.success(f"get state successfully: {state}")
        async with session.post(
            f"https://auth0.openai.com/u/login/identifier?state={state}", headers=headers, proxy=proxy,
            data={
                'state': state,
                'username': email,
                'js-available': 'false',
                'webauthn-available': 'true',
                'is-brave': 'false',
                'webauthn-platform-available': 'false',
                'action': 'default',
            }
        ) as resp:
            if resp.status != 200:
                raise ValueError(f'Status code {resp.status}: {await resp.text()}')
            logger.success("post email successfully")

        async with session.post(
            f"https://auth0.openai.com/u/login/password?state={state}", headers=headers, proxy=proxy,
            data={
                'state': state,
                'username': email,
                'password': password,
                'action': 'default',
            },
        ) as resp:
            if resp.status != 200:
                raise ValueError(f'Status code {resp.status}: {await resp.text()}')
            logger.success("post password successfully")
            if "__Secure-next-auth.session-token" not in resp.cookies:
                raise ValueError(f'Could not find __Secure-next-auth.session-token in cookies: {resp.cookies}')
            session_token = str(resp.cookies).strip("Set-Cookie:").strip().split("; ")[0].split("=")[1]
            logger.success(f"get session_token successfully: {session_token}")


class MemberGPT(TypedDict):
    running: bool
    gpt: ChatGPT


class ConversationManager(object):
    def __init__(self):
        self.data: dict[int, dict[int, MemberGPT]] = {}

    async def new(self, group: Group | int, member: Member | int):
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        if group in self.data:
            if member in self.data[group]:
                self.data[group][member]["gpt"].new_conversation()
            else:
                self.data[group][member] = {"running": False, "gpt": await create_gpt(proxies=proxy)}
        else:
            self.data[group] = {}
            self.data[group][member] = {"running": False, "gpt": await create_gpt(proxies=proxy)}

    def close(self, group: Group | int, member: Member | int):
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        if group in self.data and member in self.data[group]:
            self.data[group][member]["gpt"].close()

    async def send_message(self, group: Group | int, member: Member | int, content: str) -> str:
        if isinstance(group, Group):
            group = group.id
        if isinstance(member, Member):
            member = member.id
        if group not in self.data or member not in self.data[group]:
            _ = await self.new(group, member)
        if self.data[group][member]["running"]:
            return "我上一句话还没结束呢，别急阿~等我回复你以后你再说下一句话喵~"
        self.data[group][member]["running"] = True
        try:
            result = (await asyncio.to_thread(self.data[group][member]["gpt"].send_message, content)).content
        except StatusCodeException as e:
            result = f"发生错误：{e}，请稍后再试"
        except UnauthorizedException:
            try:
                _ = await login()
                result = "认证过期，已成功刷新Token"
            except ValueError as e:
                result = f"发生错误: {e}"
        finally:
            self.data[group][member]["running"] = False
        return result
