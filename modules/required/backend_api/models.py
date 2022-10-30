from pydantic import BaseModel


class User(BaseModel):
    username: str
    password: str


class GeneralResponse(BaseModel):
    code: int = 200
    data: list | dict = {}
    message: str = "success!"
