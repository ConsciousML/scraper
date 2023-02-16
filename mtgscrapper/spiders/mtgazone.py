"""Contains a Spider to scrap the MTGAZone website"""

import re
from typing import Generator, Dict, List, Tuple
from scrapy import Spider
from scrapy.selector import Selector

from mtgscrapper.items import MtgArticle, MtgSection, MtgBlock, Decklist
from mtgscrapper.mtg_format import FormatHandler


class MTGArenaZoneSpider(Spider):
    """Scrapy Spider to crawl the MTGAZone website"""

    name = 'mtgazone'
    start_urls = ['https://mtgazone.com/articles/']

    def __init__(
        self, *args, forbidden_tags=None, forbidden_titles=None, parse_article=True, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.forbidden_tags = forbidden_tags or ['Premium']
        self.forbidden_titles = forbidden_titles or ['Teamfight', 'Genshin', 'Spellslingers']

        if isinstance(parse_article, str) and parse_article.lower() == 'false':
            self.parse_article = False
        else:
            self.parse_article = parse_article

    def parse(self, response) -> Generator[Dict, None, None]:
        """Overrides parse method of the scrapy.Spider class

        Parses the articles from the MTGAZone website and runs a spider to crawl the content of the
        article
        """
        for article_selector in response.xpath('//article[contains(@class, "entry-card post")]'):
            title_selector = article_selector.xpath('h2[@class="entry-title"]')

            article_title = title_selector.xpath('a/text()').get().strip()
            if not self.filter_title(article_title):
                continue

            article_tags = article_selector.xpath(
                './ul[@data-type="simple:none"]/li/a/text()'
            ).getall()
            if not self.filter_tags(article_tags):
                continue

            article_url = title_selector.xpath('a/@href').get()

            author_date_selector = article_selector.xpath('./ul[@data-type="icons:none"]')
            author_name = author_date_selector.css('span').xpath('./text()').get()
            article_date = author_date_selector.css('time').xpath('./text()').get()

            article = MtgArticle(
                id_=article_selector.attrib['id'],
                title=article_title,
                date=article_date,
                url=article_url,
                tags=article_tags,
                author=author_name,
            )
            if self.parse_article:
                yield response.follow(
                    article_url, self.parse_article_content, cb_kwargs={'article': article}
                )
            else:
                yield article

        next_page = response.xpath('//a[@class="next page-numbers"]/@href').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

    def parse_article_content(self, response, article: MtgArticle) -> Generator[Dict, None, None]:
        """Crawls the content of an article

        Fills the 'content' attribute of the article and return the article as a dictionary
        """
        response.xpath('//div[contains(@class, "page-description")]/text()').get()

        content = response.xpath(
            '//article[contains(@class, "post type-post")]/div[@class="entry-content"]'
        )
        if content is None or len(content) == 0:
            raise ValueError(f'article not found for url {article.url}')

        h_tag = re.compile(r'h\d')

        section_list = []

        for selector in content.xpath(
            './p|h1|h2|h3|h4|h6|ul|div[@class="deck-block"]|figure[@class="wp-block-table"]'
        ):
            block_tag = selector.root.tag

            if h_tag.match(block_tag):  # If is a section, i.e h1, h2 ....
                section_list.append(
                    MtgSection(
                        date=article.date,
                        title=''.join(selector.xpath('.//text()').getall()),
                        level=int(block_tag[1:]),
                    )
                )
            else:
                if block_tag == 'div':
                    element = self.parse_decklist(selector, article)
                else:
                    if len(section_list) == 0:
                        section_list.append(MtgSection(date=article.date, title='', level=int(1e4)))

                    if block_tag == 'figure':
                        paragraph = ''
                        for row in selector.xpath('.//tr'):
                            paragraph += (
                                ' '.join([elt.strip() for elt in row.xpath('.//text()').getall()])
                                + '\n'
                            )

                    else:
                        paragraph = ''.join(selector.xpath('.//text()').getall())
                    element = MtgBlock(date=article.date, format_=None, text=paragraph)

                section_list[-1].content.append(element)

        self.add_package_content(section_list, article)

        format_finder = FormatHandler(search_in_text=False)
        format_finder.process_article(article)

        return article.to_dict()

    def add_package_content(self, section_list: List[MtgSection], article: MtgArticle) -> None:
        """Recursively adds the content of a section inside its attribute 'content'"""
        if len(section_list) == 0:
            raise ValueError(f'article of id {article.id} with url {article.url} is empty.')
        if len(section_list) == 1:
            article.add(section_list)
        else:
            # More than one section
            previous_section = section_list.pop(0)
            while len(section_list) > 0:
                current_section = section_list.pop(0)

                if current_section.level <= previous_section.level:
                    article.add(previous_section)

                    previous_section = current_section
                else:
                    # Current level > previous level
                    previous_section.add(current_section)

            article.add(previous_section)

    def parse_decklist(self, selector: Selector, article: MtgArticle) -> Decklist:
        """Parse decklist information and create a Decklist object"""
        best_of = selector.xpath('.//div[@class="bo"]/text()').get()
        if best_of is not None:
            best_of = int(best_of[-1])

        return Decklist(
            title=selector.xpath('.//div[@class="name"]/text()').get(),
            date=article.date,
            format_=selector.xpath('.//div[@class="format"]/text()').get(),
            deck=self.parse_cards(selector.xpath('.//div[@class="decklist main"]')),
            sideboard=self.parse_cards(selector.xpath('.//div[@class="decklist sideboard"]')),
            archetype=selector.xpath('.//div[@class="archetype"]/text()').get(),
            best_of=best_of,
        )

    def parse_cards(self, selector: Selector) -> List[Tuple]:
        """Parse the cards inside of a scrapy selector"""
        card_list = selector.xpath(
            './/div[contains(@class,"card")]/@*[name()="data-quantity" or name()="data-name"]'
        ).getall()

        card_pairs = [card_list[i : i + 2] for i in range(0, len(card_list), 2)]

        return card_pairs if len(card_pairs) > 0 else None

    def filter_title(self, article_title: str) -> bool:
        """Returns True if title is allow, False if forbidden"""
        if self.forbidden_titles is None:
            return True
        return not any(title in article_title for title in self.forbidden_titles)

    def filter_tags(self, article_tags: List[str]) -> bool:
        """Returns True if tag is allowed, False if forbidden"""
        if self.forbidden_tags is None:
            return True
        return not any(tag in article_tags for tag in self.forbidden_tags)
