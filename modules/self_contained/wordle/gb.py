from asyncio import Lock

running_mutex = Lock()
running_group = set()
