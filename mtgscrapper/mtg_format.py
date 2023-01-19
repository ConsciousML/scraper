from typing import Literal, Dict

import numpy as np

MTGFORMATS = Literal['limited', 'standard', 'historic', 'alchemy', 'explorer', 'pioneer']


class FormatHandler:

    def __init__(self, search_in_text=False) -> None:
        self.search_in_text = search_in_text

    def process_article(self, article: "MtgArticle"):
        formats = [tag.lower() for tag in article.tags if tag.lower() in MTGFORMATS.__args__]
        article.formats = formats

        known_formats = {format_: 0 for format_ in formats}

        if len(formats) == 1:
            priority_format = formats[0]
        else:
            priority_format = self.check_format_in_title(article.title)

        for content in article:
            self.process_content(content, format_=priority_format, known_formats=known_formats)

        article.formats = list(known_formats)

        if priority_format is None:
            format_occurences = np.array(list(known_formats.values()))
            sum_occurences = format_occurences.sum()
            if sum_occurences == 0:
                return

            max_key_index = format_occurences.argmax()

            format_list = list(known_formats.keys())

            if format_occurences[max_key_index] == sum_occurences:
                article.set_format(format_list[max_key_index])

    def process_content(
        self, content: "MtgSection | MtgBlock", known_formats: Dict[MTGFORMATS, int], format_=None
    ):
        if content.item_type == 'section':
            self.process_section(content, known_formats, format_=format_)
        elif content.item_type == 'block':
            self.process_block(content, known_formats, format_=format_)
        elif content.item_type == 'decklist':
            self.process_decklist(content, known_formats, format_=format_)

    def process_section(
        self, section: "MtgSection", known_formats: Dict[MTGFORMATS, int], format_=None
    ):
        if format_ is None:
            format_ = self.check_format_in_title(section.title)
            section.format_ = format_
            if format_ is not None:
                known_formats.setdefault(format_, 0)
                known_formats[format_] += 1

        section.format_ = format_

        for content in section:
            self.process_content(content, known_formats, format_=format_)

    def process_block(self, block: "MtgBlock", known_formats: Dict[MTGFORMATS, int], format_=None):
        if format_ is not None:
            block.format_ = format_
            return

        # Get most occurence of a format name in the text
        if self.search_in_text:
            format_occurences = np.array([
                block.text.lower().count(format_) for format_ in MTGFORMATS.__args__
            ])
            if format_occurences.sum() == 0:
                return None

            format_ = MTGFORMATS.__args__[format_occurences.argmax()]
            block.format_ = format_

            if format_ is not None:
                known_formats.setdefault(format_, 0)
                known_formats[format_] += 1

    def process_decklist(
        self, decklist: "MtgDecklist", known_formats: Dict[MTGFORMATS, int], format_=None
    ):
        if decklist.format_ is None:
            decklist.format_ = format_
        else:
            known_formats.setdefault(decklist.format_, 0)
            known_formats[decklist.format_] += 1

    def check_format_in_title(self, title) -> MTGFORMATS | None:
        if title is None:
            return None

        formats_in_title = [format_ for format_ in MTGFORMATS.__args__ if format_ in title.lower()]
        if len(formats_in_title) == 1:
            return formats_in_title[0]
        return None