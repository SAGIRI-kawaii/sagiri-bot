class AppCoreNotInitialized(Exception):
    """核心模块未初始化"""
    pass


class AppCoreAlreadyInitialized(Exception):
    """核心模块重复初始化"""
    pass


class AriadneAlreadyLaunched(Exception):
    """Ariadne重复启动"""
    pass


class AsyncioTasksGetResult(Exception):
    """task得到结果提前结束"""
    pass


class FrequencyLimitExceeded(Exception):
    """群组请求超出负载权重限制"""
    pass


class FrequencyLimitExceededAddBlackList(Exception):
    """单人请求超出负载权重限制并加入黑名单"""
    pass


class FrequencyLimitExceededDoNothing(Exception):
    """请求者在黑名单中不作回应"""
    pass
