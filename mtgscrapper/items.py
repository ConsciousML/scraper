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
    format_: MTGFORMATS | None = None

    def __post_init__(self):
        if self.format_ is not None:
            self.format_ = self.format_.lower()
            assert self.format_ in MTGFORMATS.__args__
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgMultiFormat(MtgItem):
    formats: List[MTGFORMATS] | None = None

    def __post_init__(self):
        assert self.formats is None or all(
            format_ in MTGFORMATS.__args__ for format_ in self.formats
        )
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgContent(MtgItem):
    content: List[MtgSection | MtgBlock] = field(default_factory=list)  # List of ids
    length = 0

    def add(self, section: MtgSection | List[MtgSection]) -> None:
        if isinstance(section, list):
            self.content += section
            self.length += len(section)
            return

        self.content.append(section)
        self.length += 1

    def __len__(self):
        self.length = len(self.content)
        return self.length

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, index):
        assert index >= 0 and index < self.length
        return self.content[index]


@dataclass(kw_only=True)
class MtgArticle(MtgTitle, MtgMultiFormat, MtgContent):
    # define the fields for your item here like:
    url: str
    tags: List[str]
    author: str
    item_type: str = 'article'

    def __post_init__(self):
        self.tags = [tag.lower() for tag in self.tags]

        # Set length of object if called with @classmethod
        len(self)

        return super().__post_init__()

    def set_format(self, format_: MTGFORMATS):
        self._set_format_recursive(self.content, format_=format_)

    def _set_format_recursive(
        self, content_list: List[MtgSection | MtgBlock | Decklist], format_: MTGFORMATS
    ):
        for content in content_list:
            content.format_ = format_
            if content.item_type == 'section':
                self._set_format_recursive(content.content, format_=format_)

    def __str__(self) -> str:
        string = f'{super().__str__()}\n'
        string += ''.join([str(section) for section in self.content])
        return string

    @classmethod
    def from_dict(cls, dict_):
        assert dict_['item_type'] == 'article'

        cls_args = dict_.copy()
        del cls_args['length']

        return cls(**cls_args)


@dataclass(kw_only=True)
class MtgSection(MtgTitle, MtgFormat, MtgContent):
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

        last_content = self.content[-1]
        if last_content.item_type == 'section' and last_content.level < section.level:
            last_content.add(section)
        else:
            super().add(section)


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
class Decklist(MtgTitle, MtgFormat):
    deck: List[str]
    sideboard: List[str] | None = None
    archetype: str | None = None
    best_of: int | None = None
    item_type: str = 'decklist'

    def __post_init__(self):
        assert len(self.deck) > 0
        #if self.best_of is not None and self.best_of == 3:
        #    assert self.sideboard is not None and len(self.sideboard) > 0
        return super().__post_init__()

    def __str__(self):
        metadata = f'Format: {self.format_}\n'
        if self.archetype is not None:
            metadata += f'Archetype: {self.archetype}\n'
        if self.best_of is not None:
            metadata += f'BO{self.best_of}\n'

        string = f'{metadata}\nDeck\n{self.cards_to_str(self.deck)}\n'
        if self.sideboard is not None:
            string += f'Sideboard\n{self.cards_to_str(self.sideboard)}\n'
        return string

    def cards_to_str(self, card_list):
        if card_list is None:
            return ''
        return ''.join([f'{nb_copies} {card_name}\n' for nb_copies, card_name in card_list])
