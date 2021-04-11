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


class OnlineNotice(BooleanCommand):
    __name__ = "online_notice"


class Debug(BooleanCommand):
    __name__ = "debug"
    level = 3


class Switch(BooleanCommand):
    __name__ = "switch"
    level = 3


class Music(AbstractCommand):
    valid_values = ["off", "wyy", "qq"]
    __name__ = "music"


class R18Process(AbstractCommand):
    valid_values = ["revoke", "flashImage"]
    __name__ = "r18_process"
    level = 3


class SpeakMode(AbstractCommand):
    valid_values = ["normal", "zuanLow", "zuanHigh", "rainbow", "chat"]
    __name__ = "speak_mode"
    level = 3


class LongTextType(AbstractCommand):
    valid_values = ["img", "text"]
    __name__ = "long_text_type"
    level = 3


command_index = {
    "repeat": Repeat(),
    "frequency_limit": FrequencyLimit(),
    "setu": Setu(),
    "real": Real(),
    "real_high_quality": RealHighQuality(),
    "bizhi": Bizhi(),
    "r18": R18(),
    "img_search": ImgSearch(),
    "bangumi_search": BangumiSearch(),
    "compile": Compile(),
    "anti_revoke": AntiRevoke(),
    "online_notice": OnlineNotice(),
    "debug": Debug(),
    "switch": Switch(),
    "music": Music(),
    "r18_process": R18Process(),
    "speak_mode": SpeakMode(),
    "long_text_type": LongTextType()
}
