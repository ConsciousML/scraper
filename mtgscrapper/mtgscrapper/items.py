# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from typing import List, Optional
from dataclasses import dataclass


@dataclass(kw_only=True)
class MtgItem:
    id: str
    title: str
    date: str
    item_type: str


@dataclass(kw_only=True)
class MtgItemFormat(MtgItem):
    format: List[str]


@dataclass(kw_only=True)
class MtgArticle(MtgItem):
    # define the fields for your item here like:
    url: str
    tags: List[str]
    author: str
    item_type: str = 'article'
    content: Optional[List[str]] = None  # List of ids


@dataclass(kw_only=True)
class MtgParagraph(MtgItemFormat):
    text: str
    title: Optional[str] = None
    parent_id: Optional[str] = None
    item_type: str = 'paragraph'


@dataclass(kw_only=True)
class MtgCard(MtgItemFormat):
    cost: str
    cart_type: str
    text: str
    set: str
    body: Optional[str] = None
    loyalty: Optional[str] = None
    item_type: str = 'card'
    # Check that boxy and loyalty are not both not null


@dataclass(kw_only=True)
class Decklist(MtgItemFormat):
    format: str
    deck: List[str]
    sideboard: List[str]
    item_type: str = 'decklist'