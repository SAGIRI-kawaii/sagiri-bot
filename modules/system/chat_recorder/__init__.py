import ujson
from loguru import logger
from sqlalchemy import select
from datetime import datetime

from launart import Launart
from graia.saya import Channel
from avilla.core import MessageReceived, Message
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .utils import seg_content
from shared.utils.control import Permission
from shared.database.interface import Database
from shared.database.tables import User, ChatRecord

channel = Channel.current()


@channel.use(ListenerSchema([MessageReceived], decorators=[Permission.require(1)]))
async def chat_recorder(message: Message):
    db = Launart.current().get_interface(Database)
    sender_data = ujson.dumps(dict(message.sender.pattern))
    user = await db.select_first(select(User).where(User.data_json == sender_data))
    if not user:
        _ = await db.add(User(data_json=sender_data))
        user = await db.select_first(select(User).where(User.data_json == sender_data))
    await db.add(
        ChatRecord(
            uid=user.id, 
            time=datetime.now(), 
            persistent_string=str(message.content),
            seg=await seg_content(message)
        )
    )
