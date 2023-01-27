# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from uuid import uuid4
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class MtgItem:
    title: str
    date: str
    item_type: str
    id_: str | None = None

    def __post_init__(self):
        if self.id_ is None:
            self.id_ = str(uuid4())


@dataclass(kw_only=True)
class MtgItemFormat(MtgItem):
    format: List[str] | None = None

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgArticle(MtgItem):
    # define the fields for your item here like:
    url: str
    tags: List[str]
    author: str
    item_type: str = 'article'
    content: List[str] = field(default_factory=list)  # List of ids

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgParagraph(MtgItemFormat):
    text: str
    title: Optional[str] = None
    parent_id: Optional[str] = None
    previous_block_id: str | None = None
    item_type: str = 'paragraph'

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class MtgCard(MtgItemFormat):
    cost: str
    cart_type: str
    text: str
    set: str
    body: str | None = None
    loyalty: str | None = None
    item_type: str = 'card'

    # Check that boxy and loyalty are not both not null

    def __post_init__(self):
        return super().__post_init__()


@dataclass(kw_only=True)
class Decklist(MtgItemFormat):
    format: str
    deck: List[str]
    sideboard: List[str]
    item_type: str = 'decklist'

    def __post_init__(self):
        return super().__post_init__()