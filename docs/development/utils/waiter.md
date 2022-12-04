# 内置中断处理

本文内可处理特定种类的中断等待事件，具体请看 官方文档"[Interrupt - 中断](https://graia.readthedocs.io/ariadne/extra/broadcast/interrupt/)"章节 或 社区文档"[请问今天你想要怎么样的涩图](https://graiax.cn/guide/interrupt_control.html)"章节

本工具类位置: `shared.utils.waiter`

> ## 等待确认（ConfirmWaiter）

用于等待一个群聊确认消息，使用方法如下：

```python
from shared.util.waiter import ConfirmWaiter


@channel.use(...)
async def foo(...):
    if await InterruptControl(saya.broadcast).wait(ConfirmWaiter(group, member, ["是", "确认", "是的", "同意", "yes", "y"])):
        print("return True")
    else:
        print("return False")
```

上面的示例是一个等待用户确认的场景，传入的参数为 `group: int | Group（要等待的用户所在群）`，`member: int | Member（要等待的用户）` 和 `confirm_words: list[str]（表示确认的词语列表）`，返回类型为 `bool`，表示确认与否，可配合 `asyncio.wait_for` 实现等待超时

> ## 私聊等待确认（FriendConfirmWaiter）

用于等待一个私聊确认消息，使用方法如下：

```python
from shared.util.waiter import FriendConfirmWaiter


@channel.use(...)
async def foo(...):
    if await InterruptControl(saya.broadcast).wait(FriendConfirmWaiter(friend, ["是", "确认", "是的", "同意", "yes", "y"])):
        print("return True")
    else:
        print("return False")
```

上面的示例是一个等待用户确认的场景，传入的参数为 `friend: int | Friend` 和 `confirm_words: list[str]（表示确认的词语列表）`，返回类型为 `bool`，表示确认与否，可配合 `asyncio.wait_for` 实现等待超时


> ## 等待图片（ImageWaiter）

用于获取用户发送的图片（一条消息内有多个只能获取一个），使用方法如下：

```python
from shared.util.waiter import ImageWaiter


@channel.use(...)
async def foo(...):
    image = await InterruptControl(saya.broadcast).wait(ImageWaiter(group, member))
    if image:
        print("这张消息里有图片！")
    else:
        print("这条消息里没有图片！")
```

上面的示例是一个等待用户确认的场景，传入的参数为 `group: int | Group（要等待的用户所在群）` 和 `member: int | Member（要等待的用户）`，返回类型为 `Image | None`，可配合 `asyncio.wait_for` 实现等待超时

!!! warning "你需要注意的"
    
    返回类型中的 `Image` 为 `graia.ariadne.message.element.Image`，并非 `PIL.Image.Image`
    
    请注意重名导致的覆盖问题，必要时候请使用 `from PIL import Image as xxx`