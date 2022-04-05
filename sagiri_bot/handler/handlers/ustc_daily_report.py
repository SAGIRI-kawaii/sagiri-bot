import asyncio
import re
import time
from lxml.html import document_fromstring
import datetime
import urllib3
import requests
from typing import Union
from threading import Thread
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Friend, FriendMessage
from graia.scheduler import GraiaScheduler
from graia.scheduler.timers import crontabify


from sagiri_bot.orm.async_orm import orm, USTCAccountInfo
from sagiri_bot.core.app_core import AppCore

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
core: AppCore = AppCore.get_core_instance()
app = core.get_app()
loop = core.get_loop()
scheduler = GraiaScheduler(loop, bcc)

MAX_RETRIES = 3
RETRY_INTERVAL = 5

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def jlu_epidemic_reporter_handler(app: Ariadne, message: MessageChain, friend: Friend):
    if result := await USTCDailyReport.handle(app, message, friend):
        await app.sendFriendMessage(friend, result)


class USTCDailyReport:
    __name__ = "USTCDailyReport"
    __description__ = "USTC 每日健康打卡"
    __usage__ = "None"

    @staticmethod
    async def handle(app: Ariadne, message: MessageChain, friend: Friend) -> Union[MessageChain, None]:

        if message.asDisplay() == "打卡":

            if res := await USTCDailyReport.data_empty_check(friend):
                await app.sendFriendMessage(friend, res)
                return None
            else:
                task = ReportTask(await USTCDailyReport.get_user_data(friend))
                task.start()


        elif message.asDisplay() == "我的信息":
            return await USTCDailyReport.show_account_info(friend)
        elif message.asDisplay().startswith("更改属性 "):
            try:
                _, attribute, value = message.asDisplay().split(" ")
                return await USTCDailyReport.update_attribute(friend, attribute, value)
            except ValueError:
                return MessageChain.create([Plain(text="格式错误！\n命令格式：更改属性 属性名 属性值\n如：更改属性 学号 PB19060000\n")])

        elif message.asDisplay() == "添加任务":
            return await USTCDailyReport.modify_scheduled(friend, True)

        elif message.asDisplay() == "移除任务":
            return await USTCDailyReport.modify_scheduled(friend, False)

        elif message.asDisplay() == "删除信息":
            return await USTCDailyReport.delete_data(friend)

        elif message.asDisplay() == "帮助":
            return MessageChain.create([
                Plain(text="打卡机器人使用帮助：\n\n"),
                Plain(text="进行打卡：发送 “打卡” 即可\n\n"),
                Plain(text="查看个人信息：发送 “我的信息” 即可\n\n"),
                Plain(text="更改个人信息：发送 “更改属性 属性名 属性值” 即可\n\n"),
                Plain(text="如：更改属性 学号 PB19060000 \n"),
                Plain(text="合法属性如下：学号、密码、现居地、宿舍楼、宿舍号、紧急联系人、与本人关系、联系人电话、是否出校报备、目的地、跨校区原因\n\n"),
                Plain(text="开启自动打卡：发送 “添加任务” 即可\n\n"),
                Plain(text="停止自动打卡：发送 “移除任务” 即可\n\n"),
                Plain(text="清空个人数据：发送 “删除信息” 即可\n\n"),
                Plain(text="更多帮助请点击 https://www.chuest.com"),
            ])

    @staticmethod
    async def data_empty_check(friend: Union[int, Friend]) -> Union[MessageChain, None]:
        attr_name = ("学号", "密码", "现居地","宿舍楼", "宿舍号", "紧急联系人", "与本人关系", "联系人电话", "是否出校报备", "目的地", "跨校区原因")
        friend = friend if isinstance(friend, int) else friend.id
        if res := await orm.fetchone(
            select(
                USTCAccountInfo.account,
                USTCAccountInfo.passwd,
                USTCAccountInfo.juzhudi,
                USTCAccountInfo.dorm_building,
                USTCAccountInfo.dorm,
                USTCAccountInfo.jinji_lxr,
                USTCAccountInfo.jinji_guanxi,
                USTCAccountInfo.jiji_mobile,
                USTCAccountInfo.ischuxiao,
                USTCAccountInfo.return_college,
                USTCAccountInfo.reason
            ).where(
                USTCAccountInfo.qq == friend
            )
        ):
            empty_list = [attr_name[i] for i in range(11) if not res[i]]
            if empty_list:
                return MessageChain.create([
                    Plain(text=f"您的信息不全，请补充下列信息：{'、'.join(empty_list)}\n"),
                    Plain(text="命令：更改属性 属性名 属性值\n"),
                    Plain(text="如：更改属性 学号 PB19060000\n"),
                    Plain(text="注：请仔细检查信息，错误信息会导致打卡失效！")
                ])
            return None
        else:
            await orm.insert_or_ignore(
                USTCAccountInfo,
                [USTCAccountInfo.qq == friend],
                {"qq": friend}
            )
            return MessageChain.create([
                Plain(text=f"您的信息不全，请补充下列信息：{'、'.join(attr_name)}\n"),
                Plain(text="补充命令：更改属性 属性名 属性值\n"),
                Plain(text="如：更改属性 学号 PB19060000\n"),
                Plain(text="注：请仔细检查信息，错误信息会导致打卡失效！")
            ])

    @staticmethod
    async def show_account_info(friend: Union[int, Friend]) -> MessageChain:
        attr_name = ("学号", "密码", "现居地", "宿舍楼", "宿舍号", "紧急联系人", "与本人关系", "联系人电话", "是否出校报备", "目的地", "跨校区原因")
        friend = friend if isinstance(friend, int) else friend.id
        result = await orm.fetchone(
            select(
                USTCAccountInfo.account,
                USTCAccountInfo.passwd,
                USTCAccountInfo.juzhudi,
                USTCAccountInfo.dorm_building,
                USTCAccountInfo.dorm,
                USTCAccountInfo.jinji_lxr,
                USTCAccountInfo.jinji_guanxi,
                USTCAccountInfo.jiji_mobile,
                USTCAccountInfo.ischuxiao,
                USTCAccountInfo.return_college,
                USTCAccountInfo.reason
            ).where(
                USTCAccountInfo.qq == friend
            )
        )
        return MessageChain.create([
            Plain(text="您的信息如下\n"),
            Plain(text='\n'.join([f"{attr_name[i]}：{result[i] if result[i] else 'None'}" for i in range(11)])),
            Plain(text="\n若想更改请使用以下命令：\n更改属性 属性名 属性值\n"),
            Plain(text="如：更改属性 学号 PB19060000\n"),
            Plain(text="注：请仔细检查信息，错误信息会导致打卡失效！")
        ])


    @staticmethod
    async def get_user_data(friend: Union[int, Friend]) -> dict:
        friend = friend if isinstance(friend, int) else friend.id
        result = await orm.fetchone(
            select(
                USTCAccountInfo.account,
                USTCAccountInfo.passwd,
                USTCAccountInfo.juzhudi,
                USTCAccountInfo.dorm_building,
                USTCAccountInfo.dorm,
                USTCAccountInfo.jinji_lxr,
                USTCAccountInfo.jinji_guanxi,
                USTCAccountInfo.jiji_mobile,
                USTCAccountInfo.ischuxiao,
                USTCAccountInfo.return_college,
                USTCAccountInfo.reason
            ).where(
                USTCAccountInfo.qq == friend
            )
        )
        return {
            "qq": friend,
            "username": result[0],
            "password": result[1],
            "juzhudi": result[2],
            "dorm_building":result[3],
            "dorm": result[4],
            "jinji_lxr": result[5],
            "jinji_guanxi": result[6],
            "jiji_mobile": result[7],
            "ischuxiao": result[8],
            "return_college": result[9],
            "reason": result[10]
        }

    @staticmethod
    async def update_attribute(friend: Union[int, Friend], attribute: str, value: str) -> MessageChain:
        attr_name_tbname = {
            "学号": "account",
            "密码": "passwd",
            "现居地": "juzhudi",
            "宿舍楼": "dorm_building",
            "宿舍号": "dorm",
            "紧急联系人": "jinji_lxr",
            "与本人关系": "jinji_guanxi",
            "联系人电话": "jiji_mobile",
            "是否出校报备": "ischuxiao",
            "目的地": "return_college",
            "跨校区原因": "reason"
        }
        if attribute not in attr_name_tbname.keys():
            return MessageChain.create([Plain(text=f"非法属性名!\n合法属性名：{'、'.join(attr_name_tbname.keys())}")])
        friend = friend if isinstance(friend, int) else friend.id
        try:
            _ = await orm.insert_or_update(USTCAccountInfo, [USTCAccountInfo.qq == friend], {"qq": friend, attr_name_tbname[attribute]: value})
            return MessageChain.create([Plain(text=f"更改成功！\n新的值：{attribute} -> {value}")])
        except Exception as e:
            return MessageChain.create([Plain(text=f"出错了！\n详情：{str(e)}\n请重试或联系管理员!")])

    @staticmethod
    async def modify_scheduled(friend: Union[int, Friend], value: bool) -> MessageChain:
        friend = friend if isinstance(friend, int) else friend.id
        if res := await USTCDailyReport.data_empty_check(friend):
            return res
        try:
            await orm.insert_or_update(USTCAccountInfo, [USTCAccountInfo.qq == friend], {"qq": friend, "scheduled": value})
            return MessageChain.create([Plain(text="添加计划任务成功！将于每日11:00进行打卡!" if value else "关闭计划任务成功！")])
        except Exception as e:
            return MessageChain.create([Plain(text=f"出错了！\n详情：{str(e)}\n请重试或联系管理员!")])

    @staticmethod
    async def delete_data(friend: Union[int, Friend]) -> MessageChain:
        friend = friend if isinstance(friend, int) else friend.id
        try:
            await orm.delete(USTCAccountInfo, [USTCAccountInfo.qq == friend])
            return MessageChain.create([Plain(text="已删除个人信息！")])
        except Exception as e:
            return MessageChain.create([Plain(text=f"出错了！\n详情：{str(e)}\n请重试或联系管理员!")])


def get_validatecode(session: requests.Session) -> str:
    import re
    import pytesseract
    from PIL import Image
    from io import BytesIO

    for attempts in range(20):
        response = session.get(
            "https://passport.ustc.edu.cn/validatecode.jsp?type=login"
        )
        stream = BytesIO(response.content)
        image = Image.open(stream)
        text = pytesseract.image_to_string(image)
        codes = re.findall(r"\d{4}", text)
        if len(codes) == 1:
            break
    return codes[0]

def login(session: requests.Session, user_data: dict):
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Origin": "https://passport.ustc.edu.cn",
            "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    session.cookies.set("lang", "zh")
    response = session.get(
        "https://weixine.ustc.edu.cn/2020/caslogin",
        headers={"Referer": "https://weixine.ustc.edu.cn/2020/login"},
    )
    root = document_fromstring(response.text)
    input = root.cssselect("input[name=CAS_LT]")
    CAS_LT = input[0].value

    response = session.post(
        "https://passport.ustc.edu.cn/login",
        data={
            "model": "uplogin.jsp",
            "service": "https://weixine.ustc.edu.cn/2020/caslogin",
            "CAS_LT": CAS_LT,
            "warn": "",
            "showCode": "1",
            "username": user_data['username'],
            "password": user_data['password'],
            "button": "",
            "LT": get_validatecode(session),
        },
        headers={
            "Referer": "https://passport.ustc.edu.cn/login?service=https://weixine.ustc.edu.cn/2020/caslogin",
        },
        allow_redirects=True,
    )
    return response

def report_health(response: requests.Response, user_data: dict, session: requests.Session):
    x = re.search(r"""<input.*?name="_token".*?>""", response.text).group(0)
    token = re.search(r'value="(\w*)"', x).group(1)

    payload = {
        "_token": token,
        "juzhudi": user_data['juzhudi'],
        "dorm_building": user_data['dorm_building'],
        "dorm": user_data['dorm'],
        "body_condition": "1",
        "body_condition_detail": "",
        "now_status": "1",
        "now_status_detail": "",
        "has_fever": "0",
        "last_touch_sars": "0",
        "last_touch_sars_date": "",
        "last_touch_sars_detail": "",
        "is_danger": "0",
        "is_goto_danger": "0",
        "jinji_lxr": user_data['jinji_lxr'],
        "jinji_guanxi": user_data['jinji_guanxi'],
        "jiji_mobile": user_data['jiji_mobile'],
        "other_detail": "",
        }

    response = session.post("https://weixine.ustc.edu.cn/2020/daliy_report", data=payload)
    content = datetime.datetime.now().strftime('%a, %b %d %H:%M:%S')
    if response.status_code != 200 or "上报成功" not in response.text:
        raise Exception('The server returned a non-successful status.')
    else:
        content +="\n健康打卡成功！"
    response = session.get(
        "https://weixine.ustc.edu.cn/2020/apply/daliy/i?t=3",
        headers={"Referer": "https://weixine.ustc.edu.cn/2020/daliy_report"}
    )

    if user_data['ischuxiao'] == '是':
        now = datetime.datetime.now()
        if int(now.strftime("%H")) >= 20:
            x = re.search(r"""<input.*?name="_token".*?>""", response.text).group(0)
            token = re.search(r'value="(\w*)"', x).group(1)

            start_date = now.strftime("%Y-%m-%d %H:%M:%S")
            end_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
            payload = {
                "_token": token,
                "start_date": start_date,
                "end_date": end_date,
                "return_college[]": user_data['return_college'].split(),
                "reason": user_data['reason'],
                "t": "3"
            }
            response = session.post("https://weixine.ustc.edu.cn/2020/apply/daliy/post", data=payload)
            if response.status_code != 200:
                raise Exception('The server returned a non-successful status.')
            else:
                content+= "\n出校报备成功！"
    return content


def one() -> str:
    """
    获取一条一言。
    :return:
    """
    url = "https://v1.hitokoto.cn/"
    res = requests.get(url).json()
    return res["hitokoto"] + "\n----" + res["from"]


def report_task(user_data: dict):
    for _ in range(MAX_RETRIES):
        try:
            session = requests.Session()
            r = login(session, user_data)
            content = report_health(r, user_data, session)
            text = one()
            content += "\n\n" + text
            return content
        except:
            time.sleep(RETRY_INTERVAL)
    return False


class ReportTask(Thread):
    def __init__(self, user_data: dict):
        Thread.__init__(self)
        self.result = False
        self.user_data = user_data

    def run(self) -> None:
        self.result = report_task(self.user_data)
        if self.result:
            asyncio.run_coroutine_threadsafe(app.sendFriendMessage(self.user_data["qq"], MessageChain.create([Plain(text=self.result)])), loop)
        else:
            asyncio.run_coroutine_threadsafe(app.sendFriendMessage(self.user_data["qq"], MessageChain.create([Plain(text="打卡失败！请再次尝试或自行前往中国科大健康打卡平台打卡！")])), loop)

    def report_success(self):
        return self.result


async def scheduled_task(app: Ariadne, friend: int):
    task = ReportTask(await USTCDailyReport.get_user_data(friend))
    task.start()


@scheduler.schedule(crontabify("0 11,21 * * *"))
async def load_scheduled_task(app: Ariadne):
    for qq in (await orm.fetchall(select(USTCAccountInfo.qq).where(USTCAccountInfo.scheduled == True))):
        await scheduled_task(app, qq[0])