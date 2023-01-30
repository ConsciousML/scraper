from typing import Literal

import numpy as np

MTGFORMATS = Literal['limited', 'standard', 'historic', 'pioneer', 'explorer', 'alchemy']


class FormatHandler:

    def __init__(self):
        pass

    def process_article(self, article: "MtgArticle"):
        formats = [tag.lower() for tag in article.tags if tag.lower() in MTGFORMATS.__args__]
        article.formats = formats

        if len(formats) == 1:
            priority_format = formats[0]
        else:
            priority_format = self.check_format_in_title(article.title)

        for content in article:
            self.process_content(content, format_=priority_format)

    def process_content(self, content: "MtgSection | MtgBlock", format_=None):
        if content.item_type == 'section':
            self.process_section(content, format_=format_)
        elif content.item_type == 'block':
            self.process_block(content, format_=format_)

    def process_section(self, section: "MtgSection", format_=None):
        if format_ is None:
            format_ = self.check_format_in_title(section.title)
            section.format_ = format_

        for content in section:
            self.process_content(content, format_=format_)

    def process_block(self, block: "MtgBlock", format_=None):
        if format_ is not None:
            block.format_ = format_
            return format_

        # Get most occurence of a format name in the text
        format_occurences = np.array([block.text.count(format_) for format_ in MTGFORMATS.__args__])
        if format_occurences.sum() == 0:
            return None

        block.format_ = MTGFORMATS.__args__[format_occurences.argmax()]
        return block.format_

    def check_format_in_title(self, title) -> MTGFORMATS | None:
        if title is None:
            return None

        formats_in_title = [format_ for format_ in MTGFORMATS.__args__ if format_ in title.lower()]
        if len(formats_in_title) == 1:
            return formats_in_title[0]
        return None