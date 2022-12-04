# 推荐的插件形式

对于插件的结构和形式，我们并不作硬性规定，但是为了能在 SAGIRI 下更好的使用，我们**推荐**以下的插件结构

!!! note "阅读前注意"

    在编写插件前，请确认你已经掌握了 Saya 的编写方法，若你还没有，请去文档学习，我们不解决如何编写的问题
    
    官方文档：[Saya](https://graia.cn/saya/)
    
    社区文档：[东西要分类好](https://graiax.cn/guide/saya.html)

## 插件目录结构

第三方插件放置于 `/modules/third_party` 文件夹中，并且插件结构如下所示

```text
modules ····························· 插件文件夹
└── third_party ····················· 第三方包文件夹
    └── your_module ················· 你的插件（包）
        ├── __init__.py ············· 插件入口文件，将自动加载此文件
        ├── utils.py ················ 插件工具类（如果有）
        └── metadata.json ··········· metadata
```

## 插件代码结构

对于 `import`，分为三个块，分别为第三方包、`graia` 相关包，`sagiri` 内置包，并按照 `import` 语句长度升序排列（这段纯为了好看，可以不看），示例如下

```python
# 第三方包
import re
import asyncio
from pathlib import Path

# graia 相关包
from creart import create
from graia.ariadne import Ariadne
from graia.saya import Saya, Channel

# sagiri 内置包
from shared.orm import orm
from shared.utils.module_related import get_command
```

对于 `saya` 的 `inline_dispatchers`，推荐使用 `Twilight`，对于需要自定义前缀的插件，使用 [get_command](/development/utils/module_related/#get_command)，示例如下：

```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module), *other_matchers])]
    )
)
async def foo(...): ...
```

对于 `saya` 的 `decorators`，SAGIRI 内置了不同的 [控制器](/development/utils/control)，可以按需使用，但是推荐所有插件都包涵 `Distribute`（账号任务分配）、`Function`（插件开关管理）和 `BlackListControl`（黑名单控制），示例如下：

```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module),
            BlackListControl.enable()
        ]
    )
)
async def foo(...): ...
```

由此，我们得到一个推荐的插件模板：

\_\_init\_\_.py:

```python
from graia.saya import Channel
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight

from shared.utils.module_related import get_command
from shared.utils.control import Distribute, Function, BlackListControl

channel = Channel.current()
channel.name("Example")
channel.author("SAGIRI-kawaii")
channel.description("这是一个示例插件")



@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        inline_dispatchers=[Twilight([get_command(__file__, channel.module), *other_matchers])]
        decorators=[
            Distribute.distribute(),
            Function.require(channel.module),
            BlackListControl.enable()
        ]
    )
)
async def foo(...): ...
```

metadata.json

```json
{
  "name": "Example",
  "version": "0.1",
  "display_name": "示例插件",
  "authors": ["SAGIRI-kawaii"],
  "description": "一个示例插件",
  "usage": ["用法1", "用法2"],
  "example": ["使用示例1", "使用示例2"],
  "icon": "",
  "prefix": ["/"],
  "triggers": ["example", "示例"],
  "metadata": {
    "uninstallable": false,
    "reloadable": true
  }
}
```

!!! note "channel.use 过长时"
    
    当一个插件需要很多的 `decoretors` 和很长的 `Twilight` 匹配格式时，`channel.use` 看起来可能很臃肿或很丑，这时可以使用 `saya_util` 来使其变得好看一些
    
    社区文档：[Saya Util —— 来点好用的缩写](https://graiax.cn/tips/shortcut.html)