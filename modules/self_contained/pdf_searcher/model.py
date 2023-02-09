from yarl import URL
from pydantic import BaseModel

from shared.utils.image import get_image


class Book(BaseModel):
    name: str
    cover: str | None
    base_url: str
    href: str
    publisher: str | None
    authors: str | None

    @property
    def display(self) -> str:
        return f"名字：{self.name}\n" + \
               (f"作者：{self.authors}\n" if self.authors else "") + \
               (f"出版社：{self.publisher}\n" if self.publisher else "") + \
               f"页面链接：{str(URL(self.href))}"

    async def get_cover(self) -> bytes:
        return await get_image(self.cover)
