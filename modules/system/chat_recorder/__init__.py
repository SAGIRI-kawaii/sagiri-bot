import ujson
from sqlalchemy import select
from datetime import datetime

from launart import Launart
from graia.saya import Channel
from graiax.shortcut.saya import listen
from avilla.core import MessageReceived, Message

from .utils import seg_content
from shared.utils.control import get_user
from shared.database.interface import Database
from shared.database.tables import User, ChatRecord

channel = Channel.current()


@listen(MessageReceived)
async def chat_recorder(message: Message):
    db = Launart.current().get_interface(Database)
    user = await get_user(message.sender)
    await db.add(
        ChatRecord(
            uid=user.id, 
            time=datetime.now(), 
            persistent_string=str(message.content),
            seg=await seg_content(message)
        )
    )
