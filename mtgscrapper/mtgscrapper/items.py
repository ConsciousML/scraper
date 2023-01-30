# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from __future__ import annotations
import re

from uuid import uuid4
from typing import List
from dataclasses import dataclass, field

from mtgscrapper.mtg_format import MTGFORMATS


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
    title: str

    def __post_init__(self):
        assert self.title is not None, 'title must have a value.'
        self.title = self.title.strip()
        return super().__post_init__()

    def __str__(self):
        return f'{self.title}\n'


@dataclass(kw_only=True)
class MtgFormat(MtgItem):
    format: List[MTGFORMATS] | None = None

    def __post_init__(self):
        assert self.format is None or self.format in MTGFORMATS.__args__
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgTitleFormat(MtgTitle, MtgFormat):

    def __post_init__(self):
        return super().__post_init__()

    def __str__(self):
        return super().__str__()


@dataclass(kw_only=True)
class MtgArticle(MtgTitle):
    # define the fields for your item here like:
    url: str
    tags: List[str]
    author: str
    item_type: str = 'article'
    priority_format: MTGFORMATS = None
    content: List[MtgSection] = field(default_factory=list)  # List of ids

    def __post_init__(self):
        return super().__post_init__()

    def __str__(self) -> str:
        string = f'{super().__str__()}\n'
        string += ''.join([str(section) for section in self.content])
        return string


@dataclass(kw_only=True)
class MtgSection(MtgTitleFormat):
    content: List[MtgBlock | MtgSection] = field(default_factory=list)
    item_type: str = 'section'
    level: int

    def __post_init__(self):
        return super().__post_init__()

    def __str__(self):
        string = f'{super().__str__()}\n'
        string += ''.join([str(item) for item in self.content])
        return string

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
        self.text = re.sub(r'(\n)\1+', r'\n', self.text).strip()
        return super().__post_init__()

    def __str__(self) -> str:
        return f'{self.text}\n\n'


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