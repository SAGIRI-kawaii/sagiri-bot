import datetime
import re

from SAGIRIBOT.basics.aio_mysql_excute import execute_sql
from SAGIRIBOT.basics.tools import filter_label


async def write_chat_record(seg, group_id: int, member_id: int, content: str) -> None:
    filter_words = re.findall(r"\[mirai:(.*?)\]", content, re.S)
    for i in filter_words:
        content = content.replace(f"[mirai:{i}]", "")
    content = content.replace("\"", " ")
    seg_result = seg.cut(content)
    seg_result = await filter_label(seg_result)
    sql = f"""INSERT INTO chatRecord 
                (`time`, groupId, memberId, content, seg)
                VALUES
                (\"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\", {group_id}, {member_id}, \"{content}\",
                \"{','.join(seg_result)}\") """
    await execute_sql(sql)
