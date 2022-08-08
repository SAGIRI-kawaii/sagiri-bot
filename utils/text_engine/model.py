from enum import Enum


class TextType(Enum):
    """Text类型"""

    H1 = {"size": 32, "spacing": 3}
    H2 = {"size": 24, "spacing": 2}
    H3 = {"size": 19, "spacing": 2}
    H4 = {"size": 15, "spacing": 1}
    H5 = {"size": 13, "spacing": 1}
    H6 = {"size": 11, "spacing": 1}
