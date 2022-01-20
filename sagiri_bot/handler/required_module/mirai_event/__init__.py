import sys

from graia.saya import Saya, Channel
from graia.ariadne.util import gen_subclass
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.broadcast.utilles import argument_signature, run_always_await_safely

from .mirai_events import *
from sagiri_bot.command_parse.utils import camel_to_underscore

saya = Saya.current()
channel = Channel.current()

channel.name("MiraiEvent")
channel.author("SAGIRI-kawaii")
channel.description("对各种事件响应")

functions = sys.modules["sagiri_bot.handler.required_module.mirai_event"].__dict__
listening_events = list(gen_subclass(GroupEvent))
listening_events.remove(GroupMessage)


@channel.use(ListenerSchema(listening_events=listening_events))
async def mirai_event(app: Ariadne, group: Group, event: GroupEvent):
    args = {"app": app, "group": group, "event": event}
    key = camel_to_underscore(event.__class__.__name__)
    if func := functions.get(key):
        argument_signatures = argument_signature(func)
        for arg in args:
            if arg not in argument_signatures or not isinstance(args[arg], argument_signatures[1].__class__):
                return None
        await run_always_await_safely(func, **args)
