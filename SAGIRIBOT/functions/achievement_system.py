from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


"""
成就系统
    涩图
        打开了新世界的大门！ 10
        里氏替换原则？ 50
        你怎么那么熟练啊！ 100
        那...那里不行！ 200
        你要对人家负责哟~ 500
        KOLSP 1000
        
    LSP龙王次数
        蛟千年化为龙！ 1
        龙无角者！ 5
        龙五百年为角龙！ 10
        千年为应龙！ 20
        浮山有龙飞入民间楼舍，须臾烟起，楼尽焚！ 50
        天神之贵者，莫贵于青龙！ 100
        
    聊天
        来聊天吧！ 10
        牛子小小说话吊吊？ 50
        我也是个百大了！ 100
        看来嘴就没闲着过！ 200
        咱老北京每天早上第一件事儿啊，就是水群！ 500
        你就是尼斯湖水怪！ 1000
         5000
         10000
    
"""

setu_achievement_code = {
    0: None,
    1: "打开了新世界的大门！",
    2: "里氏替换原则？",
    3: "你怎么那么熟练啊！",
    4: "那...那里不行！",
    5: "你要对人家负责哟~",
    6: "KOLSP"
}
setu_achievement_description = {
    0: None,
    1: "索要涩图超过10张",
    2: "索要涩图超过50张",
    3: "索要涩图超过100张",
    4: "索要涩图超过200张",
    5: "索要涩图超过500张",
    6: "索要涩图超过1000张"
}
lsp_dragon_achievement_code = {
    0: None,
    1: "蛟千年化为龙！",
    2: "龙无角者！",
    3: "龙五百年为角龙！",
    4: "千年为应龙！",
    5: "浮山有龙飞入民间楼舍，须臾烟起，楼尽焚！",
    6: "天神之贵者，莫贵于青龙！"
}
lsp_dragon_achievement_description = {
    0: None,
    1: "当选1次LSP龙王",
    2: "当选5次LSP龙王",
    3: "当选10次LSP龙王",
    4: "当选20次LSP龙王",
    5: "当选50次LSP龙王",
    6: "当选100次LSP龙王"
}
chat_achievement_code = {
    0: None,
    1: "来聊天吧！",
    2: "牛子小小说话吊吊？",
    3: "我也是个百大了！",
    4: "看来嘴就没闲着过！",
    5: "咱老北京每天早上第一件事儿啊，就是水群！",
    6: "你就是尼斯湖水怪！",
    7: "中华上下五千年，你就是文化传承者？",
    8: "我想不出词了！就这样吧！大水怪！！！"
}
chat_achievement_description = {
    0: None,
    1: "聊天超过10条",
    2: "聊天超过50条",
    3: "聊天超过100条",
    4: "聊天超过200条",
    5: "聊天超过500条",
    6: "聊天超过1000条",
    7: "聊天超过5000条",
    8: "聊天超过10000条",
}


async def get_personal_achievement(group_id: int, member_id: int):
    sql = f"select * from achievement where groupId={group_id} and memberId={member_id}"
    if result := await execute_sql(sql):
        result = result[0]
        setu = result[2]
        lsp_dragon = result[3]
        chat = result[4]
        if setu == 0 and lsp_dragon == 0 and chat == 0:
            return [
                "quoteSource",
                MessageChain.create([
                    Plain(text="你还没有获得任何成就呐~")
                ])
            ]
        msg_str = f"你已获得成就：\n\n"
        msg_str += (setu_achievement_code[setu] + "\n    " + setu_achievement_description[setu] + "\n\n") if setu != 0 else ""
        msg_str += (lsp_dragon_achievement_code[lsp_dragon] + "\n    " + lsp_dragon_achievement_description[lsp_dragon] + "\n\n") if lsp_dragon != 0 else ""
        msg_str += (chat_achievement_code[chat] + "\n    " + chat_achievement_description[chat]) if chat != 0 else ""
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text=msg_str)
            ])
        ]
    else:
        return [
            "quoteSource",
            MessageChain.create([
                Plain(text="你还没有获得任何成就呐~")
            ])
        ]


async def setu_achievement_check(group_id: int, member_id: int):
    sql = f"select setu+`real` from userCalled where groupId={group_id} and memberId={member_id}"
    # print(sql)
    result = await execute_sql(sql)
    count = result[0][0]
    # print(count)
    if count >= 1000:
        achievement_code = 6
    elif count >= 500:
        achievement_code = 5
    elif count >= 200:
        achievement_code = 4
    elif count >= 100:
        achievement_code = 3
    elif count >= 50:
        achievement_code = 2
    elif count >= 10:
        achievement_code = 1
    else:
        achievement_code = 0
    sql = f"select setu from achievement where groupId={group_id} and memberId={member_id}"
    # print(sql)
    result = await execute_sql(sql)
    if not result:
        sql = f"insert ignore into achievement (groupId, memberId) values ({group_id}, {member_id})"
        await execute_sql(sql)
        result = 0
    else:
        result = result[0][0]
    if achievement_code - result > 0:
        sql = f"update achievement set setu={achievement_code} where groupId={group_id} and memberId={member_id}"
        await execute_sql(sql)
        achievement_list = []
        for i in range(max(result + 1, 1), achievement_code + 1):
            achievement_list.append(f"{setu_achievement_code[i]}\n    {setu_achievement_description[i]}")
        achievement_text = "\n\n".join(achievement_list)
        return [
            Plain(text="恭喜 "),
            At(target=member_id),
            Plain(text=" 在本群获得成就：\n\n"),
            Plain(text=achievement_text)
        ]
    return None


async def lsp_dragon_achievement_check(group_id: int, member_id: int):
    sql = f"select count(*) from chatRecord where groupId={group_id} and memberId={member_id}"
    result = await execute_sql(sql)
    count = result[0][0]
    if count >= 100:
        achievement_code = 6
    elif count >= 50:
        achievement_code = 5
    elif count >= 20:
        achievement_code = 4
    elif count >= 10:
        achievement_code = 3
    elif count >= 5:
        achievement_code = 2
    elif count >= 1:
        achievement_code = 1
    else:
        achievement_code = 0
    sql = f"select lspDragon from achievement where groupId={group_id} and memberId={member_id}"
    # print(sql)
    result = await execute_sql(sql)
    if not result:
        sql = f"insert ignore into achievement (groupId, memberId) values ({group_id}, {member_id})"
        await execute_sql(sql)
        result = 0
    else:
        result = result[0][0]
    if achievement_code - result > 0:
        sql = f"update achievement set lspDragon={achievement_code} where groupId={group_id} and memberId={member_id}"
        await execute_sql(sql)
        achievement_list = []
        for i in range(max(result + 1, 1), achievement_code + 1):
            achievement_list.append(f"{lsp_dragon_achievement_code[i]}\n    {lsp_dragon_achievement_description[i]}")
        achievement_text = "\n\n".join(achievement_list)
        return [
            Plain(text="恭喜 "),
            At(target=member_id),
            Plain(text=" 在本群获得成就：\n\n"),
            Plain(text=achievement_text)
        ]
    return None


async def chat_achievement_check(group_id: int, member_id: int):
    sql = f"select count(*) from chatRecord where groupId={group_id} and memberId={member_id}"
    result = await execute_sql(sql)
    count = result[0][0]
    if count >= 10000:
        achievement_code = 8
    elif count >= 5000:
        achievement_code = 7
    elif count >= 1000:
        achievement_code = 6
    elif count >= 500:
        achievement_code = 5
    elif count >= 200:
        achievement_code = 4
    elif count >= 100:
        achievement_code = 3
    elif count >= 50:
        achievement_code = 2
    elif count >= 10:
        achievement_code = 1
    else:
        achievement_code = 0
    sql = f"select chat from achievement where groupId={group_id} and memberId={member_id}"
    # print(sql)
    result = await execute_sql(sql)
    if not result:
        sql = f"insert ignore into achievement (groupId, memberId) values ({group_id}, {member_id})"
        await execute_sql(sql)
        result = 0
    else:
        result = result[0][0]
    if achievement_code - result > 0:
        sql = f"update achievement set chat={achievement_code} where groupId={group_id} and memberId={member_id}"
        await execute_sql(sql)
        achievement_list = []
        for i in range(max(result + 1, 1), achievement_code + 1):
            achievement_list.append(f"{chat_achievement_code[i]}\n    {chat_achievement_description[i]}")
        achievement_text = "\n\n".join(achievement_list)
        return [
            Plain(text="恭喜 "),
            At(target=member_id),
            Plain(text=" 在本群获得成就：\n\n"),
            Plain(text=achievement_text)
        ]
    return None
