<div align="center">
    <img width="160" src="docs/sagiri.jpg" alt="logo"></br>
    <h1>SAGIRI-BOT</h1>
</div>
    
----

<div align="center">
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg"/>
    <img src="https://img.shields.io/badge/sqlalchemy-1.4.11+-orange.svg"/>
    <h3>一个基于 Mirai 和 Graia-Ariadne 的QQ机器人</h3>
    <div>SAGIRI之名取自动漫《埃罗芒阿老师》中的角色 <a href="https://zh.moegirl.org.cn/%E5%92%8C%E6%B3%89%E7%BA%B1%E9%9B%BE">和泉纱雾(Izumi Sagiri)</a></div>
    <br>
    <div>若您在使用过程中发现了bug或有一些建议，欢迎提出ISSUE、PR或加入 <a href="https://jq.qq.com/?_wv=1027&k=9hfqo8AL">QQ交流群：788031679</a> </div>
    <br>
    <div><s>来个star吧，球球惹！</s></div>
</div>


## 项目特色
- 基于Sqlalchemy的异步ORM
- 权限管理系统
- 频率限制模块
- [丰富的功能](https://sagiri-kawaii.github.io/sagiri-bot/functions/handlers/)
- 可视化管理模块【TODO】
- 基于loguru的日志系统
- 基于alembic的数据库版本管理功能

## 项目部署

[Windows部署文档](https://sagiri-kawaii.github.io/sagiri-bot/deployment/windows/)

[Linux部署文档](https://sagiri-kawaii.github.io/sagiri-bot/deployment/linux/)

[Docker部署文档](https://sagiri-kawaii.github.io/sagiri-bot/deployment/docker/)

## 使用文档

[使用文档(部分过时)](https://sagiri-kawaii.github.io/sagiri-bot/)


## 注意

- 目前机器人尚未完善，仍有许多bug存在，若您在使用中发现了bug或有更好的建议，请提ISSUE

- 目前仅对 sqlite 数据库进行了适配，使用 Mysql 以及 PostgreSQL 产生的bug可能会很多并且会导致程序无法运行，若您需要稳定的运行请使用sqlite

- 支持的数据库类型请查看sqlalchemy文档

- 若您有好的解决方法可以PR，但请保证sqlite的兼容性

## 鸣谢
- [mirai](https://github.com/mamoe/mirai) ，高效率 QQ 机器人框架 / High-performance bot framework for Tencent QQ

- [mirai-api-http](https://github.com/project-mirai/mirai-api-http) ，Mirai HTTP API (console) plugin

- [Graia Ariadne（目前使用）](https://github.com/GraiaProject/Ariadne) ，一个优雅且完备的 Python QQ 自动化框架。基于 Mirai API HTTP v2。

- [Graia Appliation（老版使用）](https://github.com/GraiaProject/Application) ，一个设计精巧, 协议实现完备的, 基于 mirai-api-http 的即时聊天软件自动化框架.

- 特别感谢 [JetBrains](https://www.jetbrains.com/?from=sagiri-bot) 为开源项目提供免费的 [PyCharm](https://www.jetbrains.com/pycharm/?from=sagiri-bot) 等 IDE 的授权  

[<img src=".github/jetbrains-variant-3.png" width="200"/>](https://www.jetbrains.com/?from=sagiri-bot)

## Stargazers over time

[![Stargazers over time](https://starchart.cc/SAGIRI-kawaii/sagiri-bot.svg)](https://starchart.cc/SAGIRI-kawaii/sagiri-bot)
