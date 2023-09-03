from loguru import logger
from typing import Literal

from graia.saya import Channel
from graiax.shortcut.saya import listen, decorate
from avilla.core import MessageReceived, Message, MessageSent, Context, Nick, Summary

from shared.utils.control import Distribute

channel = Channel.current()

LAND_DICT = {
    "qq": {
        "friend": {
            "relation": "中",
            "name": "好友",
            "child": {},
            "meta": Nick,
            "meta_name": "sender"
        },
        "group": {
            "relation": "中",
            "name": "群组",
            "meta": Summary,
            "meta_name": "scene",
            "child": {
                "member": {
                    "relation": "中",
                    "name": "群员",
                    "child": {},
                    "meta": Nick,
                    "meta_name": "sender"
                }
            }
        }
    }
}


async def parse_log(ctx: Context, message: Message, t: Literal["receive", "send"]) -> None:
    sender = message.sender
    land = sender["land"]
    content = str(message.content).replace("\n", r"\n")
    prefix = "收到" if t == "receive" else "成功发送"
    if land not in LAND_DICT:
        return logger.warning(f"{prefix}尚未支持协议<{land}>的消息：{content}")
    text = f"{prefix}来自协议 <{land}>"
    current = LAND_DICT[land]
    for key in sender.pattern:
        if key == "land":
            continue
        if key in current:
            current = current[key]
            if (t := current.get("meta")) and (tn := current.get("meta_name")):
                meta = await ctx.pull(t, getattr(message, tn))
                text += f" {current['relation']}{current['name']} <{meta.name}（{sender[key]}）>"
            else:
                text += f" {current['relation']}{current['name']} <{sender[key]}>"
            current = current["child"]
        else:
            return logger.warning(f"{prefix}尚未完全解析的协议 <{land}> 的消息：{content}")
    logger.info(text + f" 的消息：{content}")
            

@listen(MessageReceived)
@decorate(Distribute.distribute())
async def message_logger(ctx: Context, message: Message):
    await parse_log(ctx, message, "receive")
            

@listen(MessageSent)
async def message_logger(ctx: Context, message: Message):
    await parse_log(ctx, message, "send")
