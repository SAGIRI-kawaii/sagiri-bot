from graia.saya import Channel
from graia.broadcast import Broadcast
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.event.message import FriendMessage, Friend
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from .route import *
from shared.orm import orm
from .utils import generate_account
from shared.orm.tables import APIAccount
from shared.models.config import GlobalConfig
from shared.utils.waiter import FriendConfirmWaiter

saya = create(Saya)
channel = Channel.current()

channel.name("BackendAPI")
channel.author("SAGIRI-kawaii")
channel.description("管理面板后端")

config = create(GlobalConfig)


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("后端账号申请")])]
    )
)
async def account_apply(app: Ariadne, friend: Friend):
    if friend.id != config.host_qq:
        return await app.send_message(friend, "目前只有主人才有权力申请管理面板账号！")
    if await orm.fetchone(
        select(APIAccount.applicant).where(APIAccount.applicant == friend.id)
    ):
        await app.send_message(friend, "检测到数据库中已有账号，是否需要重新生成？请在30s内发送是来生成")
        try:
            if not await asyncio.wait_for(InterruptControl(create(Broadcast)).wait(FriendConfirmWaiter(friend)), 30):
                return await app.send_message(friend, "进程退出")
        except asyncio.TimeoutError:
            return await app.send_message(friend, "超时，进程退出")
    account = await generate_account(friend.id)
    await app.send_message(friend, f"已成功生成新账号：\n用户名：{account.username}\n密码：{account.password}")
