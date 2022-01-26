import sys
import inspect
from typing import Callable

from graia.saya import Saya, Channel
from graia.ariadne.util import gen_subclass
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.utilles import run_always_await_safely
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .mirai_events import *
from sagiri_bot.command_parse.utils import camel_to_underscore

saya = Saya.current()
channel = Channel.current()

channel.name("MiraiEvent")
channel.author("SAGIRI-kawaii")
channel.description("对各种事件响应")

functions = sys.modules["sagiri_bot.handler.required_module.mirai_event"].__dict__
group_listening_events = list(gen_subclass(GroupEvent))
mirai_listening_events = [i for i in gen_subclass(MiraiEvent) if not issubclass(i, GroupEvent)]
group_listening_events.remove(GroupMessage)


def argument_signature(callable_target: Callable):
    return {
        name: (
            param.annotation if param.annotation is not inspect.Signature.empty else None,
            param.default if param.default is not inspect.Signature.empty else None,
        )
        for name, param in inspect.signature(callable_target).parameters.items()
    }


@channel.use(ListenerSchema(listening_events=group_listening_events))
async def mirai_event_group(app: Ariadne, group: Group, event: GroupEvent):
    args = {"app": app, "group": group, "event": event}
    key = camel_to_underscore(event.__class__.__name__)
    if func := functions.get(key):
        argument_signatures = argument_signature(func)
        for arg in args:
            if arg in argument_signatures and not isinstance(args[arg], argument_signatures[arg][0]):
                return None
        await run_always_await_safely(func, **args)


@channel.use(ListenerSchema(listening_events=mirai_listening_events))
async def mirai_event_group(app: Ariadne, event: GroupEvent):
    args = {"app": app, "event": event}
    key = camel_to_underscore(event.__class__.__name__)
    if func := functions.get(key):
        argument_signatures = argument_signature(func)
        for arg in args:
            if arg in argument_signatures and not isinstance(args[arg], argument_signatures[arg][0]):
                return None
        await run_always_await_safely(func, **args)
