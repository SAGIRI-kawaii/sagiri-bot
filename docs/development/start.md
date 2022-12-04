# 开始

> ## 前置知识

要进行二次开发，你需要有以下语言/框架的基础

### python基础
- [python官方文档](https://docs.python.org/zh-cn/3/contents.html)

### Ariadne
- [Ariadne文档](https://graia.readthedocs.io/)
- [Graiax Community的快速实战](https://graiax.cn/)

> ## 内置 ORM

SAGIRI-BOT 内置了使用 `SQLAlchemy` 实现的 ORM 类，可用于数据库数据修改等操作，同时理论上可以适配多种数据库，用户可以自己选择喜欢的数据库种类

ORM 定义存放在 `shared.orm` 下，可自行查看源码

> ## 内置模型类

为了方便内部的数据传递，SAGIRI-BOT 中有许多的数据模型，可以从中获取到诸如设置、配置文件等的一系列信息

所有的模型类都存放在 `shared.models` 下，可自行查看源码

> ## 内置工具类

SAGIRI-BOT 提供了一系列内置工具，希望能够让开发变得更加简单、快捷，并有一个统一的风格

所有的工具都存放在 `shared.utils` 下，可自行查看源码


剩下的之后再写，咕咕咕...