from scrapy import Spider

from mtgscrapper.items import MtgArticle, MtgParagraph


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
            return

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

        stack = []

        previous_block_id = None
        for block in content.xpath('./p|h2|h3|ul'):
            block_tag = block.root.tag
            print(''.join(block.xpath('.//text()').getall()))
            if block_tag == 'h3':
                if len(stack) > 0 and stack[-1].root.tag == 'h3':
                    stack.pop()
                stack.append(block)
            elif block_tag == 'h2':
                previous_tag = None
                while previous_tag != 'h2' and len(stack) != 0:
                    previous_block = stack.pop()
                    previous_tag = previous_block.root.tag

                stack.append(block)

            else:
                paragraph = ''.join(block.xpath('.//text()').getall())

                previous_tag = None
                tag_index = len(stack) - 1

                title_stack = []
                while previous_tag != 'h2' and tag_index >= 0:
                    previous_block = stack[tag_index]
                    previous_tag = previous_block.root.tag

                    title_stack.append(''.join(previous_block.xpath('.//text()').getall()))

                    tag_index -= 1

                title = '\n'.join([title_stack[i] for i in range(len(title_stack) - 1, -1, -1)])

                mtg_paragraph = MtgParagraph(
                    title=title if len(title) > 0 else None,
                    date=article.date,
                    format=None,
                    text=paragraph,
                    parent_id=article.id_,
                    previous_block_id=previous_block_id
                )
                yield mtg_paragraph

                article.content.append(mtg_paragraph.id_)

                previous_block_id = mtg_paragraph.id_

        return article

    def filter_title(self, article_title):
        if self.forbidden_titles is None:
            return True
        return not any(title in article_title for title in self.forbidden_titles)

    def filter_tags(self, article_tags):
        if self.forbidden_tags is None:
            return True
        return not any(tag in article_tags for tag in self.forbidden_tags)