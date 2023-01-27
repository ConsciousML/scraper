# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from __future__ import annotations

from uuid import uuid4
from typing import List
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class MtgItem:
    date: str
    item_type: str
    id_: str | None = None

    def __post_init__(self):
        if self.id_ is None:
            self.id_ = str(uuid4())


@dataclass(kw_only=True)
class MtgTitle(MtgItem):
    title: str | None = None

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgFormat(MtgItem):
    format: List[str] | None = None

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgTitleFormat(MtgTitle, MtgFormat):

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgArticle(MtgTitle):
    # define the fields for your item here like:
    url: str
    tags: List[str]
    author: str
    item_type: str = 'article'
    content: List[MtgSection] = field(default_factory=list)  # List of ids

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgSection(MtgTitleFormat):
    content: List[MtgBlock | MtgSection] = field(default_factory=list)
    item_type: str = 'section'
    level: int

    def __post_init__(self):
        return super().__post_init__()

    def add(self, section: MtgSection):
        assert self.level < section.level, 'cannot add section to sub-section.'

        if len(self.content) == 0:
            self.content.append(section)
            return

        self.content[-1].add(section)


@dataclass(kw_only=True)
class MtgBlock(MtgFormat):
    text: str
    item_type: str = 'block'

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgCard(MtgBlock):
    cost: str
    cart_type: str
    set: str
    body: str | None = None
    loyalty: str | None = None
    item_type: str = 'card'

    # Check that boxy and loyalty are not both not null

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class Decklist(MtgTitleFormat):
    format: str
    deck: List[str]
    sideboard: List[str]
    item_type: str = 'decklist'

    def __post_init__(self):
        return super().__post_init__()