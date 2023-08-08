from loguru import logger

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from avilla.core import Context, MessageChain, MessageReceived, Message, Selector

channel = Channel.current()

LAND_DICT = {
    "qq": {
        "friend": {
            "relation": "中",
            "name": "好友",
            "child": {}
        },
        "group": {
            "relation": "中",
            "name": "群组",
            "child": {
                "member": {
                    "relation": "中",
                    "name": "群员",
                    "child": {}
                }
            }
        }
    }
}


def parse_log(message: Message) -> None:
    sender = message.sender
    land = sender["land"]
    content = message.content
    if land not in LAND_DICT:
        return logger.warning(f"收到尚未支持协议<{land}>的消息：{content}")
    text = f"收到来自协议 <{land}>"
    current = LAND_DICT[land]
    for key in sender.pattern:
        if key == "land":
            continue
        if key in current:
            current = current[key]
            text += f" {current['relation']}{current['name']} <{sender[key]}>"
            current = current["child"]
        else:
            return logger.warning(f"收到尚未完全解析的协议 <{land}> 的消息：{content}")
    logger.info(text + f" 的消息：{content}")
            

@channel.use(ListenerSchema([MessageReceived]))
async def message_logger(message: Message):
    parse_log(message)
