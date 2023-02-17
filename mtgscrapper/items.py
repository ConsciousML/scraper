"""Contains classes to ease the scrapping of Magic The Gathering Content"""

from __future__ import annotations
import re

from uuid import uuid4
from typing import List, Tuple, Dict, Generator
from dataclasses import dataclass, field

from mtgscrapper.mtg_format_enum import MtgFormatEnum


@dataclass(kw_only=True)
class MtgItem:
    """Abstract class for any Magic the Gathering Item"""

    date: str
    item_type: str
    id_: str | None = None

    def __post_init__(self) -> None:
        if self.id_ is None:
            self.id_ = str(uuid4())


@dataclass(kw_only=True)
class MtgTitle(MtgItem):
    """Class that has a title"""

    title: str

    def __post_init__(self) -> None:
        if self.title is None:
            raise ValueError('title must have a value.')
        self.title = self.title.strip()
        return super().__post_init__()

    def __str__(self) -> str:
        return f'{self.title}\n'


@dataclass(kw_only=True)
class MtgFormat(MtgItem):
    """Class that belongs to a given format

    For more information on Magic The Gathering Formats follow this link:
    https://magic.wizards.com/en/formats
    """

    format_: MtgFormatEnum | None = None

    def __post_init__(self) -> None:
        if self.format_ is not None:
            self.format_ = self.format_.lower()  # type: ignore
            if not MtgFormatEnum.is_format(self.format_):
                raise ValueError(f'unkown MTG format {self.format_}.')
        return super().__post_init__()

    @classmethod
    def from_dict(cls, dict_: Dict) -> MtgFormat:
        return cls(**dict_)

    def to_dict(self) -> Dict:
        return vars(self)


@dataclass(kw_only=True)
class MtgMultiFormat(MtgItem):
    """Class for objects than can contain multiple formats such as Articles"""

    formats: List[MtgFormatEnum] | None = None

    # def __post_init__(self) -> None:
    #    if self.formats is not None and not all(
    #       format_ in MtgFormatType.__args__ for format_ in self.formats
    #    ):
    #       raise ValueError(f'one of more MTG formats are unkown in {self.formats}')
    #    return super().__post_init__()


@dataclass(kw_only=True)
class MtgContent(MtgItem):
    """Class that contains nested MtgItem such as Articles or Section

    For example, a section can contain multiple blocks, sections or decklists.
    """

    content: List[MtgSection | MtgBlock | Decklist] = field(default_factory=list)  # List of ids
    length = 0

    def __post_init__(self) -> None:
        # Set length of object if called with @classmethod
        len(self)
        return super().__post_init__()

    def add(self, section: MtgSection | List[MtgSection]) -> None:
        """Adds a section to object to the class's content"""
        if isinstance(section, list):
            self.content += section
            self.length += len(section)
            return

        self.content.append(section)
        self.length += 1

    def __len__(self) -> int:
        self.length = len(self.content)
        return self.length

    def __iter__(self) -> Generator[MtgSection | MtgBlock | Decklist, None, None]:
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, index: int) -> MtgSection | MtgBlock | Decklist:
        if not 0 <= index < self.length:
            raise ValueError(f'index {index} out of range.')
        return self.content[index]

    @classmethod
    def from_dict(cls, dict_: Dict) -> MtgContent:
        """Create an instance of the class from a dictionary

        Useful to load crawled content save in the json format.
        """
        cls_args = dict_.copy()
        cls_args.pop('length', None)

        content_objects = []  # type: List[MtgItem]
        for content in dict_['content']:
            match content['item_type']:
                case 'section':
                    content_objects.append(MtgSection.from_dict(content))
                case 'block':
                    content_objects.append(MtgBlock.from_dict(content))
                case 'decklist':
                    content_objects.append(Decklist.from_dict(content))

        cls_args['content'] = content_objects

        return cls(**cls_args)

    def to_dict(self) -> Dict:
        """Creates a dictionary containing all the info from the object"""
        self_dict = vars(self)

        content_dict_list = []
        for content in self_dict['content']:
            content_dict_list.append(content.to_dict())

        self_dict['content'] = content_dict_list
        return self_dict


@dataclass(kw_only=True)
class MtgArticle(MtgTitle, MtgMultiFormat, MtgContent):
    """Class containing all the information of a Magic The Gathering article"""

    url: str
    tags: List[str]
    author: str
    item_type: str = 'article'

    def __post_init__(self) -> None:
        self.tags = [tag.lower() for tag in self.tags]

        return super().__post_init__()

    def set_format(self, format_: MtgFormatEnum) -> None:
        self._set_format_recursive(self.content, format_=format_)

    def _set_format_recursive(
        self, content_list: List[MtgSection | MtgBlock | Decklist], format_: MtgFormatEnum
    ) -> None:
        for content in content_list:
            content.format_ = format_
            if isinstance(content, MtgSection):
                self._set_format_recursive(content.content, format_=format_)

    def __str__(self) -> str:
        string = f'{super().__str__()}\n'
        string += ''.join([str(section) for section in self.content])
        return string


@dataclass(kw_only=True)
class MtgSection(MtgContent, MtgTitle, MtgFormat):  # type: ignore
    """Class materializing the Section of an Article"""

    content: List[MtgBlock | MtgSection | Decklist] = field(default_factory=list)
    item_type: str = 'section'
    level: int

    def __str__(self) -> str:
        string = f'{super().__str__()}\n'
        string += ''.join([str(item) for item in self.content])
        return string

    def add(self, section: MtgSection) -> None:  # type: ignore
        if self.level >= section.level:
            raise ValueError('cannot add section to sub-section.')

        if len(self.content) == 0:
            self.content.append(section)
            return

        last_content = self.content[-1]
        if isinstance(last_content, MtgSection) and last_content.level < section.level:
            last_content.add(section)
        else:
            super().add(section)


@dataclass(kw_only=True)
class MtgBlock(MtgFormat):
    """A block can be a paragraph of a card

    Must belong to a Mtg format
    """

    text: str
    item_type: str = 'block'

    def __post_init__(self) -> None:
        self.text = re.sub(r'(\n)\1+', r'\n', self.text).strip()
        return super().__post_init__()

    def __str__(self) -> str:
        return f'{self.text}\n\n'


@dataclass(kw_only=True)
class MtgCard(MtgBlock):
    """Contains the information of a Mtg card"""

    cost: str
    cart_type: str
    set: str
    body: str | None = None
    loyalty: str | None = None
    item_type: str = 'card'


@dataclass(kw_only=True)
class Decklist(MtgTitle, MtgFormat):
    """Contains information of a Mtg deck

    A deck contains (usually) 60 cards in the main deck and 15 cards in the sideboard (optional).
    """

    deck: List[Tuple[str, str]]
    sideboard: List[Tuple[str, str]] | None = None
    archetype: str | None = None
    best_of: int | None = None
    item_type: str = 'decklist'

    def __post_init__(self) -> None:
        if len(self.deck) == 0:
            raise ValueError('deck must contain cards')

        return super().__post_init__()

    def __str__(self) -> str:
        metadata = f'Format: {self.format_}\n'
        if self.archetype is not None:
            metadata += f'Archetype: {self.archetype}\n'
        if self.best_of is not None:
            metadata += f'BO{self.best_of}\n'

        string = f'{metadata}\nDeck\n{self.cards_to_str(self.deck)}\n'
        if self.sideboard is not None:
            string += f'Sideboard\n{self.cards_to_str(self.sideboard)}\n'
        return string

    def cards_to_str(self, card_list: List[Tuple[str, str]]) -> str:
        """Generate a string from a list of cards

        Args:
            card_list (List[Tuple[int, str]]): contains Tuples of (nb_cards, card_name).
        """
        if card_list is None:
            return ''
        return ''.join([f'{nb_copies} {card_name}\n' for nb_copies, card_name in card_list])
