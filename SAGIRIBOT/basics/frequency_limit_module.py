import time


def singleton(cls):
    # 单下划线的作用是这个变量只能在当前模块里访问,仅仅是一种提示作用
    # 创建一个字典用来保存类的实例对象
    _instance = {}

    def _singleton(*args, **kwargs):
        # 先判断这个类有没有对象
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)  # 创建一个对象,并保存到字典当中
        # 将实例对象返回
        return _instance[cls]

    return _singleton


@singleton
class GlobalFrequencyLimitDict:
    __instance = None
    __first_init = False
    frequency_limit_dict = None

    def __new__(cls, frequency_limit_dict:dict):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, frequency_limit_dict: dict):
        if not self.__first_init:
            self.frequency_limit_dict = frequency_limit_dict
            GlobalFrequencyLimitDict.__first_init = True

    def get(self, group_id: int):
        if group_id in self.frequency_limit_dict:
            print(f"group {group_id} frequency: {self.frequency_limit_dict[group_id]}")
            return self.frequency_limit_dict[group_id]
        else:
            return 10

    def set_zero(self):
        for key in self.frequency_limit_dict.keys():
            print(f"group {key} frequency count set to 0!")
            self.frequency_limit_dict[key] = 0

    def update(self, group_id: int, weight: int):
        if group_id in self.frequency_limit_dict:
            self.frequency_limit_dict[group_id] += weight
        else:
            pass


def frequency_limit(frequency_limit_instance: GlobalFrequencyLimitDict) -> None:
    """
    Frequency limit module

    Args:
        frequency_limit_instance: Frequency limit object

    Examples:
        limiter = Thread(target=frequency_limit, args=(frequency_limit_dict,))

    Return:
        None
    """
    while 1:
        time.sleep(10)
        frequency_limit_instance.set_zero()
