import json
import aiohttp
from datetime import datetime, timedelta

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne

from creart import create
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Source, Forward, ForwardNode, Image
from graia.ariadne.message.parser.twilight import (
    RegexResult,
    ArgumentMatch,
    WildcardMatch,
    ArgResult,
)

from shared.utils.text2img import md2img
from shared.models.config import GlobalConfig
from shared.utils.module_related import get_command
from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)

saya = Saya.current()
channel = Channel.current()

channel.name("Aminer")
channel.author("SAGIRI-kawaii")
channel.description("一个搜索导师信息的插件")

config = create(GlobalConfig)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-person", action="store_true", optional=True) @ "person",
                ArgumentMatch("-article", "-a", "-paper", action="store_true", optional=True) @ "article",
                ArgumentMatch("-patent", action="store_true", optional=True) @ "patent",
                WildcardMatch() @ "keyword",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("aminer", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def aminer(
    app: Ariadne,
    group: Group,
    source: Source,
    person: ArgResult,
    article: ArgResult,
    patent: ArgResult,
    keyword: RegexResult,
):
    if person.matched:
        router = "person"
    elif article.matched:
        router = "publication"
    elif patent.matched:
        router = "patent"
    else:
        router = "person"

    url = f"https://searchtest.aminer.cn/aminer-search/search/{router}"

    headers = {"Content-Type": "application/json"}

    data = {
        "query": keyword.result.display.strip(),
        "needDetails": True,
        "page": 0,
        "size": 5,
        "filters": [],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=json.dumps(data)) as resp:
            res = await resp.json()

    forward_nodes = []
    if router == "person":
        persons = res["data"]["hitList"]
        time_count = -len(persons)
        for person in persons:
            if person.get("contact"):
                institution = (
                    person["contact"]["affiliationZh"]
                    if person["contact"].get("affiliationZh")
                    else person["contact"].get("affiliation", "无数据")
                )
                bio = (
                    person["contact"]["bioZh"]
                    if person["contact"].get("bioZh")
                    else person["contact"].get("bio", "无数据")
                )
                edu = (
                    person["contact"]["eduZh"]
                    if person["contact"].get("eduZh")
                    else person["contact"].get("edu", "无数据")
                )
                work = (
                    person["contact"]["workZh"]
                    if person["contact"].get("workZh")
                    else person["contact"].get("work", "无数据")
                )
                email = person["contact"].get("email", "无数据").replace(";", "<br>")
            else:
                institution = bio = edu = work = email = "无数据"
            md = (f"<img src=\"{person.get('avatar')}\"><br>" if person.get('avatar') else '') + \
                 f"- 英文名：{person.get('name', '无数据')}<br>" + \
                 f"- 中文名：{person.get('nameZh', '无数据')}<br>" + \
                 f"- 所属机构：{institution}<br>" + \
                 f"- g-index：{person.get('gindex', '无数据')}<br>" + \
                 f"- h-index：{person.get('hindex', '无数据')}<br>" + \
                 f"- 论文总数：{person.get('npubs', '无数据')}<br>" + \
                 f"- 被引用数：{person.get('ncitation', '无数据')}<br>" + \
                 f"<br>{bio}<br><br>" + \
                 f"- 教育经历：<br>{edu}<br>" + \
                 "- 工作（经历/职位）：<br>" + \
                 f"{work}<br>" + \
                 f"邮箱：<br>{email}"
            image = await md2img(md, {"viewport": {"width": 500, "height": 10}})
            forward_nodes.append(
                ForwardNode(
                    sender_id=config.default_account,
                    time=datetime.now() + timedelta(seconds=time_count),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(Image(data_bytes=image)),
                )
            )
            time_count += 1
    elif router == "publication":
        pubs = res["data"]["hitList"]
        time_count = -len(pubs)
        for pub in pubs:
            title = pub["titleZh"] if pub.get("titleZh") else pub.get("title", "无数据")
            authors = ", ".join(
                [
                    i["nameZh"] if i.get("nameZh") else i.get("name", "无数据")
                    for i in pub.get("authors", [])
                ]
            )
            create_data = pub.get("createDate", "无数据")
            keywords = ", ".join(
                pub["keywordsZh"] if pub.get("keywordsZh") else pub.get("keywords", [])
            )
            abstract = (
                pub["pubAbstractZh"]
                if pub.get("pubAbstractZh")
                else pub.get("pubAbstract", "无数据")
            )
            md = f"- 标题：{title[0]}<br>" + \
                 f"- 作者：{authors}<br>" + \
                 f"- 创建时间：{create_data}<br>" + \
                 f"- 关键词：{keywords if keyword else '无数据'}<br>" + \
                 f"- 论文摘要：<br>{abstract}"
            image = await md2img(md, {"viewport": {"width": 500, "height": 10}})
            forward_nodes.append(
                ForwardNode(
                    sender_id=config.default_account,
                    time=datetime.now() + timedelta(seconds=time_count),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(Image(data_bytes=image)),
                )
            )
            time_count += 1
    elif router == "patent":
        patents = res["data"]["hitList"]
        time_count = -len(patents)
        for patent in patents:
            title = patent["title"].get("zh", patent["title"].get("en", "无数据"))
            inventors = ", ".join(
                [i.get("name", "无数据") for i in patent.get("inventor", [])]
            )
            assignees = ", ".join(
                [i.get("name", "无数据") for i in patent.get("assignees", [])]
            )
            abstract = patent.get("abstract", {})
            abstract = abstract.get("zh", abstract.get("en", "无数据"))
            country = patent.get("country")
            pub_num = patent.get("pub_num")
            pub_kind = patent.get("pub_kind")
            pub_auth = (
                country + pub_num + pub_kind
                if all([country, pub_num, pub_kind])
                else "无数据"
            )
            md = f"- 标题：{title}<br>" + \
                 f"- 专利号：{pub_auth}<br>" + \
                 f"- 发明人：{inventors}<br>" + \
                 f"- 专利受让人：{assignees}<br>" + \
                 f"- 专利摘要：<br>{abstract}"
            image = await md2img(md, {"viewport": {"width": 500, "height": 10}})
            forward_nodes.append(
                ForwardNode(
                    sender_id=config.default_account,
                    time=datetime.now() + timedelta(seconds=time_count),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(Image(data_bytes=image)),
                )
            )
            time_count += 1

    await app.send_group_message(group, MessageChain([Forward(node_list=forward_nodes)]), quote=source)
