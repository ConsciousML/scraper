"""Restrict the MTG format to limited string values"""
from enum import StrEnum, auto


class MtgFormatEnum(StrEnum):
    """Class that limits the values of the Mtg formats"""

    LIMITED = auto()
    STANDARD = auto()
    HISTORIC = auto()
    ALCHEMY = auto()
    EXPLORER = auto()
    PIONEER = auto()

    @classmethod
    def is_format(cls, format_: str) -> bool:
        return format_.lower() in cls._value2member_map_
