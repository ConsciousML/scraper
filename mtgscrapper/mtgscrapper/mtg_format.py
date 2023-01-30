from typing import Literal

MTGFORMATS = Literal['limited', 'standard', 'historic', 'pioneer', 'explorer', 'alchemy']


class FormatFinder:

    def __init__(self):
        pass

    def __call__(self, article: "MtgArticle"):
        format_list = MTGFORMATS.__args__
        formats = [tag.lower() for tag in article.tags if tag.lower() in format_list]

        priority_format = None
        if len(formats) == 1:
            priority_format = formats[0]
        else:
            formats_in_title = [
                format_ for format_ in format_list if format_ in article.title.lower()
            ]
            if len(formats_in_title) == 1:
                priority_format = formats_in_title[0]