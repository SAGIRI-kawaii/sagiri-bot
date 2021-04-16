import asyncio
import websockets

logs = []


async def set_log(log_str: str):
    logs.append(log_str.strip())


async def log_sender(websocket, path):
    while True:
        if logs:
            # print(logs[0])
            await websocket.send(logs[0])
            logs.pop(0)
        await asyncio.sleep(0.5)


start_server = websockets.serve(log_sender, "127.0.0.1", 8001)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
