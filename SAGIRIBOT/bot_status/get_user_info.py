from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_user_info(group_id: int, member_id: int, member_name: str, member_count: int) -> list:
    sql = f"select * from userCalled where groupId={group_id} and memberId={member_id}"
    data = await execute_sql(sql)
    if data:
        data = data[0]
        sql = f"SELECT count(*) FROM chatRecord WHERE groupId={group_id} AND memberId={member_id}"
        count = await execute_sql(sql)
        count = count[0][0]
        sql = f"SELECT count(*) FROM chatRecord WHERE groupId={group_id}"
        total_count = await execute_sql(sql)
        total_count = total_count[0][0]
        avg = round(total_count / member_count, 2)
        text = f"{member_name}，下面是你的总结哦~\n"
        text += f"\n你在本群一共发了{count}条消息，本群人均消息数为{avg}，"
        text += "好家伙您这可是真能水啊，我愿称您为水怪！\n" if count >= 2 * avg else "在群内很活跃呢！\n" if count >= avg else "看来不是很活跃呢~\n"
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
        sql = f"SELECT count(*) FROM chatRecord WHERE groupId={group_id} AND memberId={member_id}"
        count = await execute_sql(sql)
        count = count[0][0]
        sql = f"SELECT count(*) FROM chatRecord WHERE groupId={group_id}"
        total_count = await execute_sql(sql)
        total_count = total_count[0][0]
        avg = round(total_count / member_count, 2)
        text = f"{member_name}，下面是你的总结哦~\n"
        text += f"\n你在本群一共发了{count}条消息，本群人均消息数为{avg}，"
        text += "好家伙您这可是真能水啊，我愿称您为水怪！\n" if count >= 2 * avg else "在群内很活跃呢！\n" if count >= avg else "看来不是很活跃呢~\n"
        text += "\n你在本群一共要过0张图\n其中0张setu，0张real，0张bizhi\n"
        text += "再接再厉！争当LSP！\n"
        text += "\n一共@过我{0}次，"
        text += "这可不行，要多多来找纱雾玩哦~\n"
        text += "\n一共搜过0次图，"
        text += "来多多依赖纱雾嘛~\n"
        text += "\n一共点过0首歌，"
        text += "快来试试点歌吧~"
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=text)
            ])
        ]
