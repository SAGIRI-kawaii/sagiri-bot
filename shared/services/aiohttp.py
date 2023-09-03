from typing import cast

from aiohttp import ClientSession, ClientTimeout
from launart import Launart, Service


class AiohttpClientInterface:
    def __init__(self, service: "AiohttpClientService") -> None:
        self.service = service


class AiohttpClientService(Service):
    id = "http.client/aiohttp"
    session: ClientSession
    supported_interface_types = {AiohttpClientInterface}

    def __init__(self, session: ClientSession | None = None) -> None:
        self.session = cast(ClientSession, session)
        super().__init__()

    def get_interface(self, _):
        return AiohttpClientInterface(self)

    @property
    def stages(self):
        return {"preparing", "cleanup"}

    @property
    def required(self):
        return set()

    async def launch(self, _: Launart):
        async with self.stage("preparing"):
            if self.session is None:
                self.session = ClientSession(timeout=ClientTimeout(total=None))
        async with self.stage("cleanup"):
            await self.session.close()
