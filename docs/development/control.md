# 插件控制

以下控制器有部分参考自 [BlueGlassBlock](https://github.com/BlueGlassBlock)

> ## 使用方法

- 由于本文中所有的装饰器返回的都是 `Depend(func)` 形式，所以你只能在 `broadcast / saya` 中使用

- 关于 `Depend` 依赖注入，请查看 [Ariadne文档](https://graia.readthedocs.io/advance/broadcast/depend/)

- broadcast:
```python
@broadcast.receiver(GroupMessage, decorators=[Class.func()])
async def foo(...): ...
```

- saya:
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[Class.func()]
    )
)
async def foo(...): ...
```

其中 `Class` 为管理类， `func` 为管理类调用函数，具体请查看类说明

> ## Permission

权限管理类，用于获取成员权限或判断成员权限是否满足某一等级

导入：`from sagiri_bot.control import Permission`

### `Permission.get`

用途：获取成员权限

示例：`print(f"成员{member.name}权限为{Permission.get(group, member)}")`

### `Permission.require`

用途：判断成员权限是否满足某一等级

示例：
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[Permission.require(Permission.USER)]
    )
)
async def foo(...): ...
```

### 内置等级

| 名称 | 权限等级 | 等级 |
| --- | --- | --- |
| GLOBAL_BANNED | -1 | 全局黑名单（尚未实现） |
| BANNED | 0 | 群内黑名单（尚未实现） |
| USER | 1 | 普通用户 |
| GROUP_ADMIN | 2 | 管理员 |
| SUPER_ADMIN | 3 | 超级管理员 |
| MASTER | 4 | 所有者 |

### 备注

对于某些在同一module中不同等级需要不同相应的情形，可以使用 `sagiri_bot.utils.user_permission_require`

使用方法：
```python
from sagiri_bot.utils import user_permission_require


await user_permission_require(group, member, level)
```

> ## FrequencyLimit

调用频率限制类，用于限制功能调用频率

导入：`from sagiri_bot.control import FrequencyLimit`

### `FrequencyLimit.require`

用途：限制功能调用频率

示例：
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[FrequencyLimit.require("function_name", weight=1, total_weight=10, override_level=Permission.MASTER)]
    )
)
async def foo(...): ...
```

其中 `weight` 为调用一次增加的权重

`total_weight` 为10秒内本功能所接受的最大权重（若超过则会警告或拉黑一小时）

`override_level` 为不受此限制的最小权限等级（`Permission` 详见上文）

> ## Switch

机器人开关控制类

用途：实现机器人全局关闭

示例：
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[Switch.enable(response_administrator=True)]
    )
)
async def foo(...): ...
```

其中 `response_administrator` 为在机器人关闭的情况下是否响应管理员

注：此控制器功能已默认并入 `Function` 控制器，在使用 `Function` 控制器时不需再单独调用

> ## BlackListControl

黑名单控制类

用途：实现黑名单功能

示例：
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[BlackListControl.enable()]
    )
)
async def foo(...): ...
```

> ## Interval

冷却管理类

用途：实现功能调用间隔

示例：
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[Interval.require(suspend_time=10, max_exec=1, override_level=Permission.MASTER, slient=False)]
    )
)
async def foo(...): ...
```

其中 `suspend_time` 为冷却时间

`max_exec` 为在再次冷却前可使用次数

`override_level` 为可超越限制的最小等级（`Permission` 详见上文）

`silent` 为是否通知

> ## UserCalledCountControl

功能调用记录类

用途：实现功能调用计数

示例：
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[UserCalledCountControl.add(data_type=UserCalledCountControl.SETU, value=1)]
    )
)
async def foo(...): ...
```

### 内置类型

| 名称 | 类别 |
| --- | --- |
| SETU | 二次元图 |
| REAL | 三次元图 |
| BIZHI | 壁纸 |
| AT | @机器人 |
| SEARCH | 搜索功能如搜图搜番 | 
| CHAT | 聊天 |
| FUNCTIONS | 其他功能 |

### 备注

对于某些在module中触发某种条件才计入功能计数的情况，可以使用 `sagiri_bot.utils.update_user_call_count_plus`

> ## Function

单插件开关限制类

用途：实现单插件开关（替代 `SayaManager`）

示例：
```python
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[Function.require(name=channel.module, response_administrator=False, log=False, notice=False)]
    )
)
async def foo(...): ...
```

其中 `name` 为插件唯一标识，建议使用 `channel.module` 以防止插件重名的情况导致管理混乱

`response_administrator` 为在机器人关闭的情况下是否响应管理员

`log` 为收到消息时在控制台是否输出插件开关信息（不会计入log文件）

`notice` 为插件关闭时是否通知
