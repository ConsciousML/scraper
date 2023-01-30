from typing import Literal, List, Set

import numpy as np

MTGFORMATS = Literal['limited', 'standard', 'historic', 'alchemy', 'explorer', 'pioneer']


class FormatHandler:

    def __init__(self, search_in_text=False) -> None:
        self.search_in_text = search_in_text

    def process_article(self, article: "MtgArticle"):
        formats = [tag.lower() for tag in article.tags if tag.lower() in MTGFORMATS.__args__]
        article.formats = formats

        known_formats = set(formats)

        if len(formats) == 1:
            priority_format = formats[0]
        else:
            priority_format = self.check_format_in_title(article.title)

        for content in article:
            self.process_content(content, format_=priority_format, known_formats=known_formats)

        article.formats = list(known_formats)

    def process_content(
        self, content: "MtgSection | MtgBlock", known_formats: Set[MTGFORMATS], format_=None
    ):
        if content.item_type == 'section':
            self.process_section(content, known_formats, format_=format_)
        if content.item_type == 'block':
            self.process_block(content, known_formats, format_=format_)

    def process_section(self, section: "MtgSection", known_formats: Set[MTGFORMATS], format_=None):
        if format_ is None:
            format_ = self.check_format_in_title(section.title)
            section.format_ = format_
            if format_ is not None:
                known_formats.add(format_)

        section.format_ = format_

        for content in section:
            found_format = self.process_content(content, known_formats, format_=format_)
            if found_format is not None:
                known_formats.add(found_format)

    def process_block(self, block: "MtgBlock", known_formats: Set[MTGFORMATS], format_=None):
        if format_ is not None:
            block.format_ = format_
            return format_

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
                known_formats.add(format_)

        return block.format_

    def check_format_in_title(self, title) -> MTGFORMATS | None:
        if title is None:
            return None

        formats_in_title = [format_ for format_ in MTGFORMATS.__args__ if format_ in title.lower()]
        if len(formats_in_title) == 1:
            return formats_in_title[0]
        return None