from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graia.amnesia.builtins.starlette import StarletteService


class FastAPIStarletteService(StarletteService):
    def __init__(self, fastapi: FastAPI | None = None) -> None:
        self.fastapi = fastapi or FastAPI()
        self.fastapi.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        super().__init__(self.fastapi)