import asyncio
import re
import time
from asyncio import Lock
from pathlib import Path

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Voice
from graia.ariadne.message.parser.twilight import (FullMatch, RegexMatch,
                                                   RegexResult, Twilight,
                                                   WildcardMatch)
from graia.ariadne.model import Group, Member
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graiax import silkcoder
from sagiri_bot.config import GlobalConfig
from sagiri_bot.control import (BlackListControl, FrequencyLimit, Function,
                                UserCalledCountControl)

from .utils import (get_voice, mockingbird_available, models, models_available,
                    set_accuracy, set_model)

saya = Saya.current()
channel = Channel.current()
host_qq = create(GlobalConfig).host_qq

channel.name("MockingBird")
channel.author("SAGIRI-kawaii, I_love_study")
channel.description("")

mutex = Lock()
running = False

preset_path = Path(__file__).parent / "preset"

@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("纱雾说"), WildcardMatch().flags(re.DOTALL) @ "content"])],
        decorators=[
            FrequencyLimit.require("mockingbird", 3),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def mockingbird(app: Ariadne, group: Group, member: Member, source: Source, content: RegexResult):
    global running
    start_time = time.time()
    if running:
        return await app.send_group_message(
            group, MessageChain("等一下，还在跟别人说话呢，马上啊"), quote=source
        )
    content = content.result.display.strip()
    # if len(content) >= 500:
    #     return await app.sendGroupMessage(
    #         group, MessageChain("要我说的话太长了啦，要是纱雾真的努力去说的话可能会被OS杀掉的呜呜QAQ"),
    #         quote=message.getFirst(Source)
    #     )
    
    if member.id == host_qq:
        if not mockingbird_available:
            await app.send_group_message(group, MessageChain("有没有可能，不一定对，你忘记安装所需的第三方库了"))
            await app.send_group_message(group, MessageChain(Voice(path=preset_path / "ImportError.silk")))
            return
        if not models_available:
            await app.send_group_message(group, MessageChain("有没有可能，不一定对，你忘记下载模型文件了"))
            await app.send_group_message(group, MessageChain(Voice(path=preset_path / "ModelsNotFound.silk")))
            return
    elif not (mockingbird_available and models_available):
        await app.send_group_message(group, MessageChain("对不起，主人还没有把我调教好，所以还不能随便说话"))
        await app.send_group_message(group, MessageChain(Voice(path=preset_path / "UserRet.silk")))
        return

    async with mutex:
        running = True

    try:
        voice = await asyncio.get_event_loop().run_in_executor(None, get_voice, content)
    except Exception as e:
        return await app.send_group_message(group, MessageChain(str(e)), quote=source)
    finally:
        async with mutex:
            running = False
    
    await app.send_group_message(
        group,
        MessageChain([Voice(data_bytes=await silkcoder.async_encode(voice, ios_adaptive=True))])
    )
    await app.send_group_message(
        group, MessageChain(f"转换完成，用时：{time.time() - start_time}s"), quote=source
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("查看模型")])],
        decorators=[
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def show_models(app: Ariadne, group: Group):
    if len(models) == 0:
        return
    await app.send_group_message(group, MessageChain("\n".join(models)))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("修改模型"), WildcardMatch() @ "model"])],
        decorators=[
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def set_models(app: Ariadne, group: Group, source: Source, model: RegexResult):
    model = model.result.display.strip()
    if model.isnumeric() and len(models) >= int(model) > 0:
        await set_model(models[int(model)])
    elif model in models:
        await set_model(model)
    else:
        return await app.send_group_message(group, MessageChain("错误的编号或名称！"), quote=source)
    await app.send_group_message(group, MessageChain("修改成功！"), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("修改准确度"), RegexMatch("[1-9]") @ "accuracy"])],
        decorators=[
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def set_generate_accuracy(app: Ariadne, group: Group, source: Source, accuracy: RegexResult):
    accuracy = int(accuracy.result.display)
    set_accuracy(accuracy)
    await app.send_group_message(group, MessageChain(f"准确度设置成功！当前值为{accuracy}"), quote=source)
