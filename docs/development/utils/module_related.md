# 模块相关

SAGIRI-BOT 使用 `metadata.json` 来配置插件相关信息，具体定义可以查看 [PluginMeta](/development/models/config)，配置项内容可查看 [metadata.json](/configuration/#metadatajson)

> ## get_command

`metadata.json` 中支持定义插件命令前缀，但配置起作用的前提是在插件中有使用 `get_command` 来生成 `UnionMatch`，使用方法如下：

```python
from graia.saya import Channel
from graia.ariadne.message.parser.twilight import Twilight

from shared.utils.module_related import get_command

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module), *other_matchers])]
    )
)
async def foo(...): ...
```

当然，你也可以将其放在最后，实现自定义后缀（但是一般没这个需要吧）：

```python
inline_dispatchers=[Twilight([*other_matchers, get_command(__file__, channel.module)])]
```