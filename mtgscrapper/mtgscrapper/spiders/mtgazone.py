from scrapy import Spider

from mtgscrapper.items import MtgArticle


class MTGArenaZoneSpider(Spider):
    name = 'mtgazone'
    start_urls = ['https://mtgazone.com/articles/']

    def __init__(self,
                 forbidden_tags=None,
                 forbidden_titles=None,
                 parse_article=True,
                 *args,
                 **kwargs):
        super(MTGArenaZoneSpider, self).__init__(*args, **kwargs)
        self.forbidden_tags = forbidden_tags or [
            'Premium', 'Event Guides', 'Midweek Magic', 'News'
        ]
        self.forbidden_titles = forbidden_titles or [
            'Announcements', 'Teaser', 'Podcast', 'Event Guides', 'Leaks',
            'Spoiler', 'Patch Notes', 'Packs', 'Teamfight', 'Genshin', 'Brawl',
            'Compensation', 'Budget', 'Mastery', 'Tracker', 'Revealed',
            'Spellslingers'
        ]
        if isinstance(parse_article, str) and parse_article.lower() == 'false':
            self.parse_article = False
        else:
            self.parse_article = parse_article

    def parse(self, response):
        for article_selector in response.xpath(
                '//article[contains(@class, "entry-card post")]'):

            title_selector = article_selector.xpath('h2[@class="entry-title"]')

            article_title = title_selector.xpath('a/text()').get().strip()
            if not self.filter_title(article_title):
                continue

            article_tags = article_selector.xpath(
                './ul[@data-type="simple:none"]/li/a/text()').getall()
            if not self.filter_tags(article_tags):
                continue

            article_url = title_selector.xpath('a/@href').get()

            author_date_selector = article_selector.xpath(
                './ul[@data-type="icons:none"]')
            author_name = author_date_selector.css('span').xpath(
                './text()').get()
            article_date = author_date_selector.css('time').xpath(
                './text()').get()

            article = MtgArticle()
            article['id'] = article_selector.attrib['id']
            article['url'] = article_url
            article['title'] = article_title
            article['tags'] = article_tags
            article['author'] = author_name
            article['date'] = article_date

            if self.parse_article:
                yield response.follow(article_url,
                                      self.parse_article_content,
                                      cb_kwargs=dict(article=article))
            else:
                yield article

        next_page = response.xpath(
            '//a[@class="next page-numbers"]/@href').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

    def parse_article_content(self, response, article):
        return article

    def filter_title(self, article_title):
        if self.forbidden_titles is None:
            return True
        return not any(title in article_title
                       for title in self.forbidden_titles)

    def filter_tags(self, article_tags):
        if self.forbidden_tags is None:
            return True
        return not any(tag in article_tags for tag in self.forbidden_tags)