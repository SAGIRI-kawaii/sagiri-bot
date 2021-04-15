class AppCoreNotInitialized(Exception):
    """核心模块未初始化"""
    pass


class AppCoreAlreadyInitialized(Exception):
    """核心模块重复初始化"""
    pass


class GraiaMiraiApplicationAlreadyLaunched(Exception):
    """GraiaMiraiApplication重复启动"""
    pass


class AsyncioTasksGetResult(Exception):
    """task得到结果提前结束"""
    pass
