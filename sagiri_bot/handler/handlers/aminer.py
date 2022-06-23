import json
from datetime import datetime, timedelta

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Source, Forward, ForwardNode, Plain, Image
from graia.ariadne.message.parser.twilight import FullMatch, RegexResult, ArgumentMatch, WildcardMatch, ArgResult

from sagiri_bot.core.app_core import AppCore
from utils.text_engine.adapter import GraiaAdapter
from utils.text_engine.text_engine import TextEngine
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("Aminer")
channel.author("SAGIRI-kawaii")
channel.description("一个搜索导师信息的插件")

config = AppCore.get_core_instance().get_config()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/aminer"),
                ArgumentMatch("-person", action="store_true", optional=True) @ "person",
                ArgumentMatch("-article", "-a", "-paper", action="store_true", optional=True) @ "article",
                ArgumentMatch("-patent", action="store_true", optional=True) @ "patent",
                WildcardMatch() @ "keyword"
            ])
        ],
        decorators=[
            FrequencyLimit.require("aminer", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH)
        ]
    )
)
async def aminer(
    app: Ariadne,
    group: Group,
    message: MessageChain,
    person: ArgResult,
    article: ArgResult,
    patent: ArgResult,
    keyword: RegexResult
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

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "query": keyword.result.asDisplay().strip(),
        "needDetails": True,
        "page": 0,
        "size": 5,
        "filters": []
    }
    print(data)

    async with get_running(Adapter).session.post(url=url, headers=headers, data=json.dumps(data)) as resp:
        res = await resp.json()
        print(res)

    forward_nodes = []
    if router == "person":
        persons = res["data"]["hitList"]
        time_count = -len(persons)
        for person in persons:
            institution = person["contact"]["affiliationZh"] if person["contact"].get("affiliationZh") else person['contact'].get('affiliation', '无数据')
            bio = person['contact']['bioZh'].replace('<br>', '\n') if person["contact"].get("bioZh") else person['contact'].get('bio', '无数据')
            edu = person['contact']['eduZh'].replace('<br>', '\n') if person["contact"].get("eduZh") else person['contact'].get('edu', '无数据')
            work = person['contact']['workZh'].replace('<br>', '\n') if person["contact"].get("workZh") else person['contact'].get('work', '无数据')
            forward_nodes.append(
                ForwardNode(
                    senderId=config.bot_qq,
                    time=datetime.now() + timedelta(seconds=time_count),
                    senderName="纱雾酱",
                    messageChain=MessageChain([
                        Image(data_bytes=TextEngine([GraiaAdapter(MessageChain([
                            Image(url=person.get("avatar")) if person.get("avatar") else Plain(""),
                            Plain("\n") if person.get("avatar") else Plain(""),
                            Plain(f"英文名：{person.get('name', '无数据')}\n"),
                            Plain(f"中文名：{person.get('nameZh', '无数据')}\n"),
                            Plain(f"所属机构：{institution}\n"),
                            Plain(f"g-index：{person.get('gindex', '无数据')}\n"),
                            Plain(f"h-index：{person.get('hindex', '无数据')}\n"),
                            Plain(f"论文总数：{person.get('npubs', '无数据')}\n"),
                            Plain(f"被引用数：{person.get('ncitation', '无数据')}\n"),
                            Plain(bio),
                            Plain(f"\n教育经历：\n{edu}"),
                            Plain(f"\n工作（经历/职位）：\n"),
                            Plain(work),
                            Plain("\n邮箱：\n"),
                            Plain(person['contact'].get('email', '无数据').replace(';', '\n'))
                        ]))], min_width=1080).draw())
                    ])
                )
            )
            time_count += 1
    elif router == "publication":
        pubs = res["data"]["hitList"]
        time_count = -len(pubs)
        for pub in pubs:
            title = pub['titleZh'] if pub.get("titleZh") else pub.get("title", "无数据")
            authors = ", ".join(
                [i["nameZh"] if i.get("nameZh") else i.get("name", "无数据") for i in pub.get("authors", [])]
            )
            create_data = pub.get("createDate", "无数据")
            keywords = ", ".join(pub["keywordsZh"] if pub.get("keywordsZh") else pub.get("keywords", []))
            abstract = pub['pubAbstractZh'] if pub.get("pubAbstractZh") else pub.get("pubAbstract", "无数据")
            forward_nodes.append(
                ForwardNode(
                    senderId=config.bot_qq,
                    time=datetime.now() + timedelta(seconds=time_count),
                    senderName="纱雾酱",
                    messageChain=MessageChain([
                        Image(data_bytes=TextEngine([GraiaAdapter(MessageChain([
                            Plain(f"标题：{title[0]}\n"),
                            Plain(f"作者：{authors}\n"),
                            Plain(f"创建时间：{create_data}\n"),
                            Plain(f"关键词：{keywords if keyword else '无数据'}\n"),
                            Plain(f"论文摘要：\n{abstract}")
                        ]))], min_width=1080).draw())
                    ])
                )
            )
            time_count += 1
    elif router == "patent":
        patents = res["data"]["hitList"]
        time_count = -len(patents)
        for patent in patents:
            title = patent["title"].get("zh", patent["title"].get("en", "无数据"))
            inventors = ", ".join([i.get("name", "无数据") for i in patent.get("inventor", [])])
            assignees = ", ".join([i.get("name", "无数据") for i in patent.get("assignees", [])])
            abstract = patent.get("abstract", {})
            abstract = abstract.get("zh", abstract.get("en", "无数据"))
            country = patent.get("country")
            pub_num = patent.get("pub_num")
            pub_kind = patent.get("pub_kind")
            pub_auth = country + pub_num + pub_kind if all([country, pub_num, pub_kind]) else "无数据"
            forward_nodes.append(
                ForwardNode(
                    senderId=config.bot_qq,
                    time=datetime.now() + timedelta(seconds=time_count),
                    senderName="纱雾酱",
                    messageChain=MessageChain([
                        Image(data_bytes=TextEngine([GraiaAdapter(MessageChain([
                            Plain(f"标题：{title}\n"),
                            Plain(f"专利号：{pub_auth}\n"),
                            Plain(f"发明人：{inventors}\n"),
                            Plain(f"专利受让人：{assignees}\n"),
                            Plain(f"专利摘要：\n{abstract}")
                        ]))], min_width=1080).draw())
                    ])
                )
            )
            time_count += 1

    await app.sendGroupMessage(group, MessageChain([Forward(nodeList=forward_nodes)]), quote=message.getFirst(Source))
