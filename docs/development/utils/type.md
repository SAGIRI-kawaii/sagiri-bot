# 类型判断

对于一些由 `Twilight` 匹配得到的数据（如 `ArgResult`），我们可能希望他是某一种类型（比如 `float`），但是如果在参数很多的时候，代码就会显得又长又乱，在这时你就可以使用内置的类型判断函数

有关 `Twilight` 可观看 官方文档"[Twilight - 混合式消息链处理器](https://graia.readthedocs.io/ariadne/feature/twilight/)"章节 或 社区文档"[Twilight](https://graiax.cn/guide/message_parser/twilight.html)"章节

本工具类位置: `shared.utils.type`

> ## MessageChain 类型转换

对于 `MessageChain`，我们可以使用 `parse_type` 函数对其进行类型判断和取值

使用示例如下：

```python
from shared.utils.type import parse_type


m1 = MessageChain("114.514")

res1 = parse_type(m1, int, 0)    # res1 = 114

res2 = parse_type(m1, float, 0.0)    # res2 = 114.514

m2 = MessageChain("test")

res3 = parse_type(m2, int, 1)   # res3 = 1

res4 = parse_type(m2, float, 0.1)   # res3 = 0.1
```

可以看到，我们通过一个函数就进行了值的转换，如果他可以进行转换，则返回转换后的值，如果不可以，则返回设定好的默认值

函数定义为 `def parse_type(message: MessageChain, res_type: Type[T], default_value: Optional[T] = None) -> T`

> ## Match 类型转换

`Match` 为 `Twilight` 返回的匹配类型，对于 `Match`，我们的转换方法与 `MessageChain` 完全相同，只是函数名变为 `parse_match_type`
