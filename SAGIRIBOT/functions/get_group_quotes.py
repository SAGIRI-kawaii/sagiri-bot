from graia.application.event.messages import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_group_quotes(group_id: int, memberList, nickname, Type, status) -> list:
    if status == "nickname":
        sql = "select memberId from nickname where groupId=%d and nickname='%s'" % (group_id, nickname[0])
        member_id = await execute_sql(sql)
        member_id = member_id[0][0]
        # print(quotes)
        if member_id is None:
            return [
                "None",
                MessageChain.create([
                    Plain(text="%s是谁我不知道呐~快来添加别名吧~" % nickname[0])
                ])
            ]
    elif status == "memberId":
        member_id = nickname
    elif status == "none":
        pass
    if Type == "random":
        sql = "select * from celebrityQuotes where groupId=%d order by rand() limit 1" % group_id
        quotes = await execute_sql(sql)[0]
        # print(quotes)
        if quotes is None:
            return [
                "None",
                MessageChain.create([
                    Plain(text="本群还没有群语录哟~快来添加吧~")
                ])
            ]
        else:
            member_id = quotes[1]  # 说出名言的人
            content = quotes[2]  # 内容，可能为地址/文本
            quote_format = quotes[3]  # 语录形式 img/text
            if quote_format == "text":
                return [
                    Plain(text=content),
                    Plain(text="\n————%s" % qq2name(memberList, member_id))
                ]
            elif quote_format == "img":
                return [
                    # At(target=memberId),
                    Image.fromFileSystem(content)
                    # Plain(text="\n————%s"%qq2name(memberList,memberId))
                ]
            else:
                return [Plain(text="quoteFormat error!(%s)" % quote_format)]
    elif Type == "all":
        sql = "select * from celebrityQuotes where groupId=%s and memberId=%s" % (group_id, member_id[0])
        quotes = await execute_sql(sql)
        if quotes is None:
            return [Plain(text="%s还没有语录哦~快来添加吧~" % nickname[0])]
        msg = [Plain(text="%s语录\n" % nickname[0])]
        index = 1
        for i in quotes:
            # print(i)
            content = i[2]  # 内容，可能为地址/文本
            quote_format = i[3]  # 语录形式 img/text
            if quote_format == "text":
                msg.append(Plain(text="%d.%s\n" % (index, content)))
            elif quote_format == "img":
                msg.append(Plain(text="%d.\n" % index))
                msg.append(Image.fromFileSystem(content))
                msg.append(Plain(text="\n"))
            else:
                return [Plain(text="quoteFormat error!(%s)" % quote_format)]
            index += 1
        return msg
    else:
        sql = "select * from celebrityQuotes where groupId=%s and memberId=%s order by rand() limit 1" % (
            group_id, member_id[0])
        quotes = await execute_sql(sql)
        if quotes is None:
            return [Plain(text="%s还没有语录哦~快来添加吧~" % nickname[0])]
        content = quotes[2]  # 内容，可能为地址/文本
        quote_format = quotes[3]  # 语录形式 img/text
        if quote_format == "text":
            return [
                Plain(text=content),
                Plain(text="\n————%s" % nickname[0])
            ]
        elif quote_format == "img":
            return [
                # At(target=memberId),
                Image.fromFileSystem(content)
                # Plain(text="\n————%s"%qq2name(memberList,memberId))
            ]
        else:
            return [Plain(text="quoteFormat error!(%s)" % quote_format)]
