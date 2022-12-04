# 文件相关

此文件中存储了异步读取文件的函数

> ## read_file

使用方法：

```python
from shared.utils.files import read_file


async def foo(...):
    content = await read_file(path)
```

> ## load_yaml

使用方法：

```python
from shared.utils.files import load_yaml


async def foo(...):
    config = await load_yaml(path)
```
