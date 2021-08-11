import re
import json
import time
import urllib3
import requests
from typing import Union
from threading import Thread
from sqlalchemy import select

from graia.saya import Saya, Channel
from graia.scheduler import GraiaScheduler
from graia.scheduler.timers import crontabify
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.event import BaseEvent, BaseDispatcher
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Friend, FriendMessage
from graia.broadcast.interfaces.dispatcher import DispatcherInterface

from SAGIRIBOT.Core.AppCore import AppCore
from SAGIRIBOT.ORM.AsyncORM import orm, JLUEpidemicAccountInfo

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
core: AppCore = AppCore.get_core_instance()
loop = core.get_loop()
scheduler = GraiaScheduler(loop, bcc)

MAX_RETRIES = 15
TIMEOUT = 10
RETRY_INTERVAL = 10
DEBUG = 0
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def jlu_epidemic_reporter_handler(app: GraiaMiraiApplication, message: MessageChain, friend: Friend):
    if result := await JLUEpidemicReporterHandler.handle(app, message, friend):
        await app.sendFriendMessage(friend, result)


class ProcessTermination(BaseEvent):
    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface):
            pass


class JLUEpidemicReporterHandler:
    __name__ = "JLUEpidemicReporterHandler"
    __description__ = "JLU打卡handler"
    __usage__ = "None"

    @staticmethod
    async def handle(app: GraiaMiraiApplication, message: MessageChain, friend: Friend) -> Union[MessageChain, None]:
        @Waiter.create_using_function([FriendMessage])
        def confirm(event: FriendMessage, waiter_friend: Friend, waiter_message: MessageChain):
            if waiter_friend.id == friend.id:
                if waiter_message.asDisplay() == "确认":
                    return event
                else:
                    return ProcessTermination()
        if message.asDisplay() == "打卡":
            await app.sendFriendMessage(
                friend,
                MessageChain.create([Plain(text="本机器人所收集数据仅会用于吉林大学疫情打卡使用，代码以AGPLV3协议开源于https://github.com/SAGIRI-kawaii/sagiri-bot/blob/master/SAGIRIBOT/Handler/Handlers/JLUEpidemicReporterHandler.py")])
            )
            if res := await JLUEpidemicReporterHandler.data_empty_check(friend):
                await app.sendFriendMessage(friend, res)
                return None
            else:
                await app.sendFriendMessage(friend, await JLUEpidemicReporterHandler.show_and_confirm_account_info(friend))
                inc = InterruptControl(bcc)
                result = await inc.wait(confirm)
                if not isinstance(result, ProcessTermination):
                    await app.sendFriendMessage(friend, MessageChain.create([Plain(text="正在启动打卡进程...")]))
                    task = ReportTask(await JLUEpidemicReporterHandler.get_user_data(friend))
                    task.start()
                    task.join()
                    if task.report_success():
                        return MessageChain.create([Plain(text="打卡成功！请前往吉林大学微服务小程序检查是否打卡成功！")])
                    else:
                        return MessageChain.create([Plain(text="打卡失败！请再次尝试或自行前往吉林大学微服务小程序打卡！")])
                else:
                    return MessageChain.create([Plain(text="用户未确认，中止进程，若想再次进行打卡，请发送 “打卡”")])
        elif message.asDisplay() == "我的信息":
            return await JLUEpidemicReporterHandler.show_account_info(friend)
        elif message.asDisplay().startswith("更改属性 "):
            try:
                _, attribute, value = message.asDisplay().split(" ")
                return await JLUEpidemicReporterHandler.update_attribute(friend, attribute, value)
            except ValueError:
                return MessageChain.create([Plain(text="格式错误！\n命令格式：更改属性 属性名 属性值\n如：更改属性 姓名 张三")])
        elif message.asDisplay() == "添加计划任务":
            return await JLUEpidemicReporterHandler.modify_scheduled(friend, True)
        elif message.asDisplay() == "移除计划任务":
            return await JLUEpidemicReporterHandler.modify_scheduled(friend, False)
        elif message.asDisplay() == "删除数据":
            inc = InterruptControl(bcc)
            result = await inc.wait(confirm)
            if not isinstance(result, ProcessTermination):
                return await JLUEpidemicReporterHandler.delete_data(friend)
            else:
                return MessageChain.create([Plain(text="用户未确认，中止进程，若想再次进行打卡，请发送 “打卡”")])
        elif message.asDisplay() == "帮助":
            return MessageChain.create([
                Plain(text="打卡机器人使用帮助：\n"),
                Plain(text="进行打卡：发送 ”打卡“ 即可\n\n"),
                Plain(text="查看个人信息：发送 ”我的信息“ 即可\n\n"),
                Plain(text="更改个人信息：发送 ”更改属性 属性名 属性值“ 即可\n"),
                Plain(text="如：更改属性 姓名 张三\n"),
                Plain(text="注：合法属性如下：姓名、用户名、密码、校区编号、宿舍楼编号、寝室编号\n\n"),
                Plain(text="开启自动打卡：发送 ”添加计划任务“ 即可\n\n"),
                Plain(text="停止自动打卡：发送 ”移除计划任务“ 即可\n\n"),
                Plain(text="清空个人数据：发送 ”删除数据“ 即可")
            ])

    @staticmethod
    async def data_empty_check(friend: Union[int, Friend]) -> Union[MessageChain, None]:
        attr_name = ("姓名", "用户名", "密码", "校区编号", "宿舍楼编号", "寝室编号")
        friend = friend if isinstance(friend, int) else friend.id
        if res := await orm.fetchone(
            select(
                JLUEpidemicAccountInfo.name,
                JLUEpidemicAccountInfo.account,
                JLUEpidemicAccountInfo.passwd,
                JLUEpidemicAccountInfo.campus_id,
                JLUEpidemicAccountInfo.dorm_id,
                JLUEpidemicAccountInfo.room_id
            ).where(
                JLUEpidemicAccountInfo.qq == friend
            )
        ):
            empty_list = [attr_name[i] for i in range(6) if not res[i]]
            if empty_list:
                return MessageChain.create([
                    Plain(text=f"您的信息不全，请补充下列信息：{'、'.join(empty_list)}\n"),
                    Plain(text="命令：更改属性 属性名 属性值\n"),
                    Plain(text="如：更改属性 姓名 张三"),
                    Plain(text="注：请仔细检查信息，错误信息会导致打卡失效！")
                ])
            return None
        else:
            await orm.insert_or_ignore(
                JLUEpidemicAccountInfo,
                [JLUEpidemicAccountInfo.qq == friend],
                {"qq": friend}
            )
            return MessageChain.create([
                Plain(text=f"您的信息不全，请补充下列信息：{'、'.join(attr_name)}\n"),
                Plain(text="补充命令：更改属性 属性名 属性值\n"),
                Plain(text="如：更改属性 姓名 张三\n"),
                Plain(text="注：请仔细检查信息，错误信息会导致打卡失效！")
            ])

    @staticmethod
    async def show_and_confirm_account_info(friend: Union[int, Friend]) -> MessageChain:
        attr_name = ("姓名", "用户名", "密码", "校区编号", "宿舍楼编号", "寝室编号")
        friend = friend if isinstance(friend, int) else friend.id
        result = await orm.fetchone(
            select(
                JLUEpidemicAccountInfo.name,
                JLUEpidemicAccountInfo.account,
                JLUEpidemicAccountInfo.passwd,
                JLUEpidemicAccountInfo.campus_id,
                JLUEpidemicAccountInfo.dorm_id,
                JLUEpidemicAccountInfo.room_id
            ).where(
                JLUEpidemicAccountInfo.qq == friend
            )
        )
        return MessageChain.create([
            Plain(text="您的信息如下，请确认无误后发送 “确认”\n"),
            Plain(text='\n'.join([f"{attr_name[i]}：{result[i]}" for i in range(6)])),
            Plain(text="\n若想更改请使用以下命令：\n更改属性 属性名 属性值\n"),
            Plain(text="如：更改属性 姓名 张三\n"),
            Plain(text="注：请仔细检查信息，错误信息会导致打卡失效！")
        ])

    @staticmethod
    async def show_account_info(friend: Union[int, Friend]) -> MessageChain:
        attr_name = ("姓名", "用户名", "密码", "校区编号", "宿舍楼编号", "寝室编号")
        friend = friend if isinstance(friend, int) else friend.id
        result = await orm.fetchone(
            select(
                JLUEpidemicAccountInfo.name,
                JLUEpidemicAccountInfo.account,
                JLUEpidemicAccountInfo.passwd,
                JLUEpidemicAccountInfo.campus_id,
                JLUEpidemicAccountInfo.dorm_id,
                JLUEpidemicAccountInfo.room_id
            ).where(
                JLUEpidemicAccountInfo.qq == friend
            )
        )
        return MessageChain.create([
            Plain(text="您的信息如下\n"),
            Plain(text='\n'.join([f"{attr_name[i]}：{result[i] if result[i] else 'None'}" for i in range(6)])),
            Plain(text="\n若想更改请使用以下命令：\n更改属性 属性名 属性值\n"),
            Plain(text="如：更改属性 姓名 张三\n"),
            Plain(text="注：请仔细检查信息，错误信息会导致打卡失效！")
        ])


    @staticmethod
    async def get_user_data(friend: Union[int, Friend]) -> dict:
        friend = friend if isinstance(friend, int) else friend.id
        result = await orm.fetchone(
            select(
                JLUEpidemicAccountInfo.name,
                JLUEpidemicAccountInfo.account,
                JLUEpidemicAccountInfo.passwd,
                JLUEpidemicAccountInfo.campus_id,
                JLUEpidemicAccountInfo.dorm_id,
                JLUEpidemicAccountInfo.room_id
            ).where(
                JLUEpidemicAccountInfo.qq == friend
            )
        )
        return {
            "username": result[1],
            "password": result[2],
            "fields": {
                "fieldSQxq": result[3],
                "fieldSQgyl": result[4],
                "fieldSQqsh": result[5]
            },
            "name": result[0]
        }

    @staticmethod
    async def update_attribute(friend: Union[int, Friend], attribute: str, value: str) -> MessageChain:
        attr_name_tbname = {
            "姓名": "name",
            "用户名": "account",
            "密码": "passwd",
            "校区编号": "campus_id",
            "宿舍楼编号": "dorm_id",
            "寝室编号": "room_id"
        }
        if attribute not in attr_name_tbname.keys():
            return MessageChain.create([Plain(text=f"非法属性名!\n合法属性名：{'、'.join(attr_name_tbname.keys())}")])
        friend = friend if isinstance(friend, int) else friend.id
        try:
            _ = await orm.insert_or_update(JLUEpidemicAccountInfo, [JLUEpidemicAccountInfo.qq == friend], {"qq": friend, attr_name_tbname[attribute]: value})
            return MessageChain.create([Plain(text=f"更改成功！\n新的值：{attribute} -> {value}")])
        except Exception as e:
            return MessageChain.create([Plain(text=f"出错了！\n详情：{str(e)}\n请重试或联系管理员!")])

    @staticmethod
    async def modify_scheduled(friend: Union[int, Friend], value: bool) -> MessageChain:
        friend = friend if isinstance(friend, int) else friend.id
        if res := await JLUEpidemicReporterHandler.data_empty_check(friend):
            return res
        try:
            await orm.insert_or_update(JLUEpidemicAccountInfo, [JLUEpidemicAccountInfo.qq == friend], {"qq": friend, "scheduled": value})
            return MessageChain.create([Plain(text="成功加入计划任务！将于每日9: 05与21：05进行打卡!" if value else "成功关闭计划任务！")])
        except Exception as e:
            return MessageChain.create([Plain(text=f"出错了！\n详情：{str(e)}\n请重试或联系管理员!")])

    @staticmethod
    async def delete_data(friend: Union[int, Friend]) -> MessageChain:
        friend = friend if isinstance(friend, int) else friend.id
        try:
            await orm.delete(JLUEpidemicAccountInfo, [JLUEpidemicAccountInfo.qq == friend])
        except Exception as e:
            return MessageChain.create([Plain(text=f"出错了！\n详情：{str(e)}\n请重试或联系管理员!")])


def report_task(user_data: dict, transaction: str = "BKSMRDK") -> bool:
    for _ in range(MAX_RETRIES):
        try:
            s = requests.Session()
            s.headers.update({'Referer': 'https://ehall.jlu.edu.cn/'})
            s.verify = False

            # logger.info(f"Authenticating user: {user_data['username']}({user_data['name']})")
            r = s.get('https://ehall.jlu.edu.cn/sso/login#/', timeout=TIMEOUT)
            pid = re.search('(?<=name="pid" value=")[a-z0-9]{8}', r.text)[0]
            # logger.debug(f"PID: {pid}")

            post_payload = {'username': user_data['username'], 'password': user_data['password'], 'pid': pid}
            r = s.post('https://ehall.jlu.edu.cn/sso/login', data=post_payload, timeout=TIMEOUT)
            # print(r.status_code)

            # logger.info('Requesting form...')
            r = s.get(f"https://ehall.jlu.edu.cn/infoplus/form/{transaction}/start", timeout=TIMEOUT)
            csrf_token = re.search('(?<=csrfToken" content=").{32}', r.text)[0]
            # logger.debug(f"CSRF: {csrf_token}")

            post_payload = {'idc': transaction, 'csrfToken': csrf_token}
            r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/start', data=post_payload, timeout=TIMEOUT)
            sid = re.search('(?<=form/)\\d*(?=/render)', r.text)[0]
            # logger.debug(f"Step ID: {sid}")

            post_payload = {'stepId': sid, 'csrfToken': csrf_token}
            r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/render', data=post_payload, timeout=TIMEOUT)
            data = json.loads(r.content)['entities'][0]

            # logger.info('Submitting form...')

            payload_1 = data['data']
            payload_1['fieldZtw'] = '1'
            if payload_1['fieldXY1'] == '1':
                payload_1['fieldZhongtw'] = '1'
            if payload_1['fieldXY2'] == '1':
                payload_1['fieldWantw'] = '1'
            payload_1["fieldDJXXyc"] = '1'
            for k, v in user_data['fields'].items():
                payload_1[k] = v
            # payload_1["fieldDJXXyc"] = '1'
            payload_1 = json.dumps(payload_1)
            payload_2 = ','.join(data['fields'].keys())
            post_payload = {
                'actionId': 1,
                'formData': payload_1,
                'nextUsers': '{}',
                'stepId': sid,
                'timestamp': int(time.time()),
                'boundFields': payload_2,
                'csrfToken': csrf_token
            }
            # logger.debug(f"Payload: {post_payload}")
            r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/doAction', data=post_payload, timeout=TIMEOUT)
            # logger.debug(f"Result: {r.text}")
            if json.loads(r.content)['ecode'] != 'SUCCEED':
                raise Exception('The server returned a non-successful status.')
            # logger.info('Success!')
            return True
        except:
            # logger.error(traceback.format_exc())
            time.sleep(RETRY_INTERVAL)
    return False


class ReportTask(Thread):
    def __init__(self, user_data: dict, transaction: str = "BKSMRDK"):
        Thread.__init__(self)
        self.result = False
        self.user_data = user_data
        self.transaction = transaction

    def run(self) -> None:
        self.result = report_task(self.user_data, self.transaction)

    def report_success(self) -> bool:
        return self.result


async def scheduled_task(app: GraiaMiraiApplication, friend: int):
    await app.sendFriendMessage(friend, MessageChain.create([Plain(text="正在启动打卡进程...")]))
    task = ReportTask(await JLUEpidemicReporterHandler.get_user_data(friend))
    task.start()
    task.join()
    if task.report_success():
        await app.sendFriendMessage(friend, MessageChain.create([Plain(text="打卡成功！请前往吉林大学微服务小程序检查是否打卡成功！")]))
    else:
        await app.sendFriendMessage(friend, MessageChain.create([Plain(text="打卡失败！请再次尝试或自行前往吉林大学微服务小程序打卡！")]))


@scheduler.schedule(crontabify("21 9/21 * * *"))
async def load_scheduled_task(app: GraiaMiraiApplication):
    for qq in (await orm.fetchall(select(JLUEpidemicAccountInfo.qq).where(JLUEpidemicAccountInfo.scheduled == True))):
        await scheduled_task(app, qq[0])
