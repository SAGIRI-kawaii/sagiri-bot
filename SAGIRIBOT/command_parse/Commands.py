import re
import sys
import inspect
from abc import ABC, abstractmethod


class Command(ABC):
    """
    Command interface，
    """

    @abstractmethod
    def is_valid(self, value) -> bool:
        pass


class AbstractCommand(Command):
    __name__ = ""
    level = 2
    valid_values = []

    def is_valid(self, value) -> bool:
        return value in self.valid_values


class BooleanCommand(AbstractCommand):
    valid_values = [True, False]


class StringCommand(AbstractCommand):
    pass


class Repeat(BooleanCommand):
    __name__ = "repeat"


class FrequencyLimit(BooleanCommand):
    __name__ = "frequency_limit"


class Setu(BooleanCommand):
    __name__ = "setu"


class Real(BooleanCommand):
    __name__ = "real"


class RealHighQuality(BooleanCommand):
    __name__ = "real_high_quality"


class Bizhi(BooleanCommand):
    __name__ = "bizhi"


class R18(BooleanCommand):
    __name__ = "r18"
    level = 3


class ImgSearch(BooleanCommand):
    __name__ = "img_search"


class BangumiSearch(BooleanCommand):
    __name__ = "bangumi_search"


class Compile(BooleanCommand):
    __name__ = "compile"


class AntiRevoke(BooleanCommand):
    __name__ = "anti_revoke"


class AntiFlashImage(BooleanCommand):
    __name__ = "anti_flash_image"


class Dice(BooleanCommand):
    __name__ = "dice"


class AvatarFunc(BooleanCommand):
    __name__ = "avatar_func"


class OnlineNotice(BooleanCommand):
    __name__ = "online_notice"


class Debug(BooleanCommand):
    __name__ = "debug"
    level = 3


class Switch(BooleanCommand):
    __name__ = "switch"
    level = 3


class Music(StringCommand):
    valid_values = ["off", "wyy", "qq"]
    __name__ = "music"


class R18Process(StringCommand):
    valid_values = ["revoke", "flashImage", "noProcess"]
    __name__ = "r18_process"
    level = 3


class SpeakMode(StringCommand):
    valid_values = ["normal", "zuanLow", "zuanHigh", "rainbow", "chat"]
    __name__ = "speak_mode"
    level = 3


class LongTextType(StringCommand):
    valid_values = ["img", "text"]
    __name__ = "long_text_type"
    level = 3


class Voice(StringCommand):
    valid_values = ["off", "0", "1", "2", "3", "4", "5", "6", "7", "1001", "1002", "1003", "1050", "1051", "101001", "101002", "101003", "101004", "101005", "101006", "101007", "101008", "101009", "101010", "101011", "101012", "101013", "101014", "101015", "101016", "101017", "101018", "101019", "101050", "101051"]
    __name__ = "voice"
    level = 3


# command_index = {
#     "repeat": Repeat(),
#     "frequency_limit": FrequencyLimit(),
#     "setu": Setu(),
#     "real": Real(),
#     "real_high_quality": RealHighQuality(),
#     "bizhi": Bizhi(),
#     "r18": R18(),
#     "img_search": ImgSearch(),
#     "bangumi_search": BangumiSearch(),
#     "compile": Compile(),
#     "anti_revoke": AntiRevoke(),
#     "anti_flashimage": AntiFlashImage(),
#     "online_notice": OnlineNotice(),
#     "debug": Debug(),
#     "switch": Switch(),
#     "music": Music(),
#     "r18_process": R18Process(),
#     "speak_mode": SpeakMode(),
#     "long_text_type": LongTextType(),
#     "dice": Dice(),
#     "avatar_func": AvatarFunc(),
#     "voice": Voice()
# }

command_index = {
    k: v for k, v in [
        (re.sub(r"(?P<key>[A-Z])", r"_\g<key>", class_name).strip("_").lower(), class_())
        for class_name, class_ in inspect.getmembers(sys.modules[__name__], inspect.isclass)
        if issubclass(class_, BooleanCommand) or issubclass(class_, StringCommand)
    ]
}
print(command_index)
