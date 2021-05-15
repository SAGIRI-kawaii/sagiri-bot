# 功能扩展

如何更改本机器人中加载的功能

## Saya
想要加载Saya插件，只需要将插件本体（文件/包）放入 `modules` 文件夹，默认自动加载 `modules` 文件夹下所有插件，之后可能会添加控制模块加载的方法

## Handler
BOT中自带的Handler已经是Saya的形式，若您想移除一些功能，只需将功能（文件/包）移除出 `SAGIRIBOT.Handler.Handlers` 