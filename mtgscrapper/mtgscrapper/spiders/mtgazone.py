import re
from scrapy import Spider

from mtgscrapper.items import MtgArticle, MtgSection, MtgBlock
from mtgscrapper.mtg_format import MTGFORMATS, FormatFinder


class MTGArenaZoneSpider(Spider):
    name = 'mtgazone'
    start_urls = ['https://mtgazone.com/articles/']

    def __init__(
        self, forbidden_tags=None, forbidden_titles=None, parse_article=True, *args, **kwargs
    ):
        super(MTGArenaZoneSpider, self).__init__(*args, **kwargs)
        self.forbidden_tags = forbidden_tags or ['Premium', 'Event Guides', 'Midweek Magic', 'News']
        self.forbidden_titles = forbidden_titles or [
            'Announcements', 'Teaser', 'Podcast', 'Event Guides', 'Leaks', 'Spoiler', 'Patch Notes',
            'Packs', 'Teamfight', 'Genshin', 'Brawl', 'Compensation', 'Budget', 'Mastery',
            'Tracker', 'Revealed', 'Spellslingers', 'Codes'
        ]
        if isinstance(parse_article, str) and parse_article.lower() == 'false':
            self.parse_article = False
        else:
            self.parse_article = parse_article

    def parse(self, response):
        for article_selector in response.xpath('//article[contains(@class, "entry-card post")]'):

            title_selector = article_selector.xpath('h2[@class="entry-title"]')

            article_title = title_selector.xpath('a/text()').get().strip()
            if not self.filter_title(article_title):
                continue

            article_tags = article_selector.xpath('./ul[@data-type="simple:none"]/li/a/text()'
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
                author=author_name
            )

            if self.parse_article:
                yield response.follow(
                    article_url, self.parse_article_content, cb_kwargs=dict(article=article)
                )
            else:
                yield article

        next_page = response.xpath('//a[@class="next page-numbers"]/@href').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

    def parse_article_content(self, response, article):

        response.xpath('//div[contains(@class, "page-description")]/text()').get()

        content = response.xpath(
            '//article[contains(@class, "post type-post")]/div[@class="entry-content"]'
        )
        if content is None or len(content) == 0:
            raise ValueError(f'article not found for url {article.url}')

        h_tag = re.compile(r'h\d')

        section_list = []

        for block in content.xpath('./p|h1|h2|h3|h4|h6|ul'):
            block_tag = block.root.tag

            if h_tag.match(block_tag):
                section_list.append(
                    MtgSection(
                        date=article.date,
                        title=''.join(block.xpath('.//text()').getall()),
                        level=int(block_tag[1:])
                    )
                )
            else:
                if len(section_list) == 0:
                    section_list.append(MtgSection(date=article.date, title='', level=int(1e4)))

                paragraph = ''.join(block.xpath('.//text()').getall())

                section_list[-1].content.append(
                    MtgBlock(
                        date=article.date,
                        format=None,
                        text=paragraph,
                    )
                )

        if len(section_list) == 0:
            raise ValueError(f'article of id {article.id} with url {article.url} is empty.')
        elif len(section_list) == 1:
            article.content = section_list
        else:
            # More than one section
            previous_section = section_list.pop(0)
            while len(section_list) > 0:
                current_section = section_list.pop(0)

                if current_section.level <= previous_section.level:
                    article.content.append(previous_section)

                    previous_section = current_section
                else:
                    # Current level > previous level
                    previous_section.add(current_section)
            article.content.append(previous_section)

        format_finder = FormatFinder()
        format_finder(article)

        return article

    def filter_title(self, article_title):
        if self.forbidden_titles is None:
            return True
        return not any(title in article_title for title in self.forbidden_titles)

    def filter_tags(self, article_tags):
        if self.forbidden_tags is None:
            return True
        return not any(tag in article_tags for tag in self.forbidden_tags)