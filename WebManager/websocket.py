import asyncio
import websockets
from loguru import logger
from websockets.exceptions import ConnectionClosedOK

from SAGIRIBOT.utils import get_config

logs = []


async def set_log(log_str: str):
    logs.append(log_str.strip())


async def log_sender(websocket, path):
    while True:
        if logs:
            try:
                await websocket.send(logs[0])
                logs.pop(0)
            except ConnectionClosedOK as e:
                logger.warning(f"websocket断开连接: {e}")
                return
        await asyncio.sleep(0.01)


start_server = websockets.serve(log_sender, "127.0.0.1", 8001)
if get_config("webManagerApi"):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
