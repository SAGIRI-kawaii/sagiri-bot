import os
from datetime import datetime
from typing import Literal

import psutil
from launart import Launart, Launchable
from loguru import logger

_code_map: dict[int, str] = {
    0: "<green>正常</green>",
    1: "<red>意外错误</red>",
}

_launch_time: dict[str, tuple[float, Literal[0, 1]]] = {}


def add_launch_time(module: str, _time: float, status: Literal[0, 1]):
    _launch_time[module] = (_time, status)


class LaunchTimeService(Launchable):
    id = "sagiri.core.launch_time"

    @property
    def required(self):
        return set()

    @property
    def stages(self):
        return {"blocking"}

    async def launch(self, _mgr: Launart):
        async with self.stage("blocking"):
            current_proc = psutil.Process(os.getpid())
            create_time = datetime.fromtimestamp(current_proc.create_time())
            delta = datetime.now() - create_time
            name_length = max(len(module) for module in _launch_time.keys())
            module_sum = sum(_time for _time, _ in _launch_time.values())
            time_length = max(len(str(_time)) for _time, _ in _launch_time.values())
            top = (
                f"\n\n<red>本次启动耗时 </red><yellow>{delta.total_seconds()}"
                f"</yellow> <red>秒，模块加载耗时</red> <yellow>{module_sum:.6f}"
                f"</yellow> <red>秒</red>\n\n<red>{'模块':<{name_length}}</red> |"
                f" <yellow>{'耗时':<{time_length + 2}}</yellow> | <yellow>状态</yellow>\n"
            )

            for module, (_time, code) in sorted(
                _launch_time.items(), key=lambda x: x[1], reverse=True
            ):
                top += (
                    f"<red>{module:<{name_length}}</red> "
                    f"| <yellow>{_time:0<{time_length}}</yellow> <red>s</red> "
                    f"| {_code_map[code]}\n"
                )

            logger.opt(colors=True).success(top)
