from typing import Union
from pydantic import BaseModel


class User(BaseModel):
    user_name: str
    password: str


class GeneralResponse(BaseModel):
    code: int = 200
    data: Union[list, dict] = {}
    message: str = "success!"
