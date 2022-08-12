from typing import List
from unwind import get_report, ReportFlag

from creart import create
from graia.ariadne import Ariadne
from graia.saya import Saya, Channel
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.exception import AccountMuted, UnknownTarget

from sagiri_bot.config import GlobalConfig
from utils.text_engine.text_engine import TextEngine

saya = create(Saya)
channel = Channel.current()

channel.name("ExceptionCatcher")
channel.author("SAGIRI-kawaii")
channel.description("一个能够捕获错误并将其转为图片发给主人的插件")

config: GlobalConfig = create(GlobalConfig)


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(event: ExceptionThrowed):
    app = Ariadne.current()
    if isinstance(event.event, ExceptionThrowed):
        return
    if isinstance(
        event.exception,
        (AccountMuted, UnknownTarget)
    ):
        return
    return await app.send_friend_message(
        config.host_qq,
        MessageChain(
            Image(
                data_bytes=TextEngine(
                    generate_reports(event.exception),
                    min_width=4096,
                    spacing=5,
                    line_spacing=10,
                ).draw()
            )
        ),
    )


def generate_reports(exception: BaseException) -> List[str]:
    strings = [f"报错: {exception.__class__.__name__} {exception}"]
    for index, report in enumerate(get_report(exception)):
        if report.flag == ReportFlag.ACTIVE:
            strings.append(
                f"\n----------report[{index}]----------\n"
                f"原因: 主动抛出异常 {report.flag}\n"
                f"位置: {report.info.name}, line {report.info.line}, in {report.info.file}\n"
                f"代码: {report.info.code}\n"
                f"错误类型: {report.type}\n"
                f"错误内容: {report.content}"
            )
        elif report.flag in (ReportFlag.OPERATE, ReportFlag.UNKNOWN):
            strings.append(
                f"\n----------report[{index}]----------\n"
                f"原因: 操作出错 {report.flag}\n"
                f"位置: {report.info.name}, line {report.info.line}, in {report.info.file}\n"
                f"代码: {report.info.code}\n"
                f"参数: {report.args}"
            )
        else:
            strings.append(
                f"\n----------report[{index}]----------\n"
                f"原因: 执行代码 {report.flag}\n"
                f"位置: {report.info.name}, line {report.info.line}, in {report.info.file}\n"
                f"代码: {report.info.code}\n"
                f"执行对象: {report.callable}\n"
                f"参数: {report.args}"
            )
    return strings
