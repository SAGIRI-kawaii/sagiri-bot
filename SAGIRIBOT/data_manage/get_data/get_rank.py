from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import At

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_rank(group_id: int, memberList: list) -> list:
    sql = "select * from dragon where groupId=%d order by count desc" % group_id
    lsp_rank = await execute_sql(sql)
    print(lsp_rank)
    msg = []
    text = "啊嘞嘞，从启动到现在都没有人要过涩图的嘛!呜呜呜~\n人家。。。人家好寂寞的，快来找我玩嘛~"
    if lsp_rank == ():
        return [
            "None",
            MessageChain.create([
                Plain(text=text)
            ])
        ]
    else:
        lsp_champion_count = lsp_rank[0][3]
        if lsp_champion_count == 0:
            return [
                "None",
                MessageChain.create([
                    Plain(text=text)
                ])
            ]
        text = "目前lsp排行榜："
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
                add_bool=False
                last = i[3]
            text += "\n%i.%-20s %3d" % (index, qq2name(memberList,i[2]), i[3])
        msg.append(Plain(text=text))
        return msg