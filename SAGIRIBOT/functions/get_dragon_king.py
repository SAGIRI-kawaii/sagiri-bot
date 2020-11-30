import datetime

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At
from graia.application import GraiaMiraiApplication

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_dragon_king(group_id: int, app: GraiaMiraiApplication) -> MessageChain:
    """
    Get daily dragon king

    Args:
        group_id: Group Id
        app: Graia app

    Examples:
        msg = await get_dragon_king()

    Return:
        MessageChain: message to send
    """
    sql = "select * from dragon where groupId=%d order by count desc" % group_id
    lsp_rank = await execute_sql(sql)
    print(lsp_rank)
    msg = []
    text = "啊嘞嘞，从启动到现在都没有人要过涩图的嘛!呜呜呜~\n人家。。。人家好寂寞的，快来找我玩嘛~"
    if lsp_rank == ():
        return MessageChain.create([
                Plain(text=text)
            ])
    else:
        time_now = datetime.datetime.now().strftime("%Y-%m-%d")
        lsp_champion_count = lsp_rank[0][3]
        if lsp_champion_count == 0:
            return MessageChain.create([
                    Plain(text=text)
                ])
        text = "今天是%s\n" % time_now
        text += "今日获得老色批龙王称号的是：\n"
        msg.append(Plain(text=text))
        lsp_champion_count = lsp_rank[0][3]
        if lsp_champion_count == 0:
            text = "啊嘞嘞，从启动到现在都没有人要过涩图的嘛!呜呜呜~\n人家。。。人家好寂寞的，快来找我玩嘛~"
            return MessageChain.create([
                Plain(text=text)
            ])
        for i in lsp_rank:
            if i[3] == lsp_champion_count:
                if i[2] != 80000000:
                    msg.append(At(target=i[2]))
                    msg.append(Plain(text="\n"))
                else:
                    msg.append(Plain(text="@匿名LSP\n"))
            else:
                break
        text = "让我们恭喜他！\n今日lsp排行榜："
        msg.append(Plain(text=text))
        text = ""
        index = 0
        add_bool = False
        add = 0
        last = -1
        for i in lsp_rank:
            if i[3] == 0:
                break
            if i[3] == last:
                add += 1
                add_bool = True
            else:
                if add_bool:
                    index += add
                index += 1
                add = 0
                add_bool = False
                last = i[3]
            member = await app.getMember(group_id, i[2])
            text += "\n%i.%-20s %3d" % (index, member.name, i[3])
        msg.append(Plain(text=text))
        return MessageChain.create(msg)
