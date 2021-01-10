from graia.application import GraiaMiraiApplication
from graia.application.event.messages import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def get_group_quotes(group_id: int, app: GraiaMiraiApplication, nickname: str, quote_type: str, source_status: str) -> list:
    member_id = None
    if source_status == "nickname":
        sql = "select memberId from nickname where groupId=%d and nickname='%s'" % (group_id, nickname)
        member_id = await execute_sql(sql)
        print(member_id)
        # print(quotes)
        if member_id == ():
            return [
                "None",
                MessageChain.create([
                    Plain(text="%s是谁我不知道呐~快来添加别名吧~" % nickname)
                ])
            ]
        member_id = member_id[0][0]
    elif source_status == "memberId":
        member_id = int(nickname)
    elif source_status == "None":
        pass

    if quote_type == "random":
        sql = "select * from celebrityQuotes where groupId=%d order by rand() limit 1" % group_id
        quotes = await execute_sql(sql)
        quotes = quotes[0]
        # print(quotes)
        if quotes is None:
            return [
                "None",
                MessageChain.create([
                    Plain(text="本群还没有群语录哟~快来添加吧~")
                ])
            ]
        else:
            member_id = int(quotes[1])  # 说出名言的人
            content = quotes[2]  # 内容，可能为地址/文本
            quote_format = quotes[3]  # 语录形式 img/text
            if quote_format == "text":
                member = await app.getMember(group_id, member_id)
                return [
                    "None",
                    MessageChain.create([
                        Plain(text=content),
                        Plain(text="\n————%s" % member.name)
                    ])
                ]
            elif quote_format == "img":
                return [
                    "None",
                    MessageChain.create([
                        Image.fromLocalFile(content)
                    ])
                ]
            else:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="quoteFormat error!(%s)" % quote_format)
                    ])
                ]
    elif quote_type == "all":
        sql = "select * from celebrityQuotes where groupId=%s and memberId=%s" % (group_id, member_id)
        quotes = await execute_sql(sql)
        if quotes is None:
            return [
                "None",
                MessageChain.create([
                    Plain(text="%s还没有语录哦~快来添加吧~" % nickname[0])
                ])
            ]
        member = await app.getMember(group_id, member_id)
        msg = [Plain(text="%s语录\n" % member.name)]
        index = 1
        for i in quotes:
            # print(i)
            content = i[2]  # 内容，可能为地址/文本
            quote_format = i[3]  # 语录形式 img/text
            if quote_format == "text":
                msg.append(Plain(text="%d.%s\n" % (index, content)))
            elif quote_format == "img":
                msg.append(Plain(text="%d.\n" % index))
                msg.append(Image.fromLocalFile(content))
                msg.append(Plain(text="\n"))
            else:
                return [
                    "None",
                    MessageChain.create([
                        Plain(text="quoteFormat error!(%s)" % quote_format)
                    ])
                ]
            index += 1
        return [
            "None",
            MessageChain.create(msg)
        ]
    elif quote_type == "select":
        sql = "select * from celebrityQuotes where groupId=%s and memberId=%s order by rand() limit 1" % (
            group_id, member_id)
        quotes = await execute_sql(sql)
        quotes = quotes[0]
        if quotes is None:
            return [
                "None",
                MessageChain.create([
                    Plain(text="%s还没有语录哦~快来添加吧~" % nickname[0])
                ])
            ]
        content = quotes[2]  # 内容，可能为地址/文本
        quote_format = quotes[3]  # 语录形式 img/text
        print(group_id, member_id)
        member = await app.getMember(group_id, member_id)
        if quote_format == "text":
            return [
                "None",
                MessageChain.create([
                    Plain(text=content),
                    Plain(text="\n————%s" % member.name)
                ])
            ]
        elif quote_format == "img":
            return [
                "None",
                MessageChain.create([
                    Image.fromLocalFile(content)
                ])
            ]
        else:
            return [
                "None",
                MessageChain.create([
                    Plain(text="quoteFormat error!(%s)" % quote_format)
                ])
            ]
    else:
        return ["None"]
