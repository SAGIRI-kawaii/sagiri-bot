from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_user_info(group_id: int, member_id: int, member_name: str) -> list:
    sql = f"select * from userCalled where groupId={group_id} and memberId={member_id}"
    data = await execute_sql(sql)
    if data:
        data = data[0]
        sql = f"SELECT count(*) FROM chatRecord WHERE groupId={group_id} AND memberId={member_id}"
        count = await execute_sql(sql)
        count = count[0][0]
        text = f"{member_name}，下面是你的总结哦~\n"
        text += f"\n你在本群一共发了{count}条消息，"
        text += "老水怪了！\n" if count > 100 else "看来不是很活跃呢~\n"
        text += f"\n你在本群一共要过{data[2] + data[3] + data[4]}张图\n其中{data[2]}张setu，{data[3]}张real，{data[4]}张bizhi\n"
        text += "看来你真是个十足的LSP呢！\n" if data[2] + data[3] >= 10 else "再接再厉！争当LSP！\n"
        text += f"\n一共@过我{data[5]}次，"
        text += "看来你很喜欢找我玩呐~嘿嘿，被纱雾的美貌迷住了吧~\n" if data[5] >= 10 else "这可不行，要多多来找纱雾玩哦~\n"
        text += f"\n一共搜过{data[6]}次图，"
        text += "看来纱雾也被人依赖了呢！嘿嘿，开心！\n" if data[6] >= 5 else "来多多依赖纱雾嘛~\n"
        text += f"\n一共点过{data[9]}首歌，"
        text += "看来你很喜欢听歌呐！" if data[9] > 0 else "快来试试点歌吧~"
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=text)
            ])
        ]
    else:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="啊嘞嘞，没有找到你的信息呐~好怪哦~")
            ])
        ]
