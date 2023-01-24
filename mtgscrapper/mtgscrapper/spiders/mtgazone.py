from scrapy import Spider

from mtgscrapper.items import MtgArticle


class MTGArenaZoneSpider(Spider):
    name = 'mtgazone'
    start_urls = ['https://mtgazone.com/articles/']

    def parse(self, response):
        for article_selector in response.xpath(
                '//article[contains(@class, "entry-card post")]'):

            title_selector = article_selector.xpath('h2[@class="entry-title"]')

            article_url = title_selector.xpath('a/@href').get()
            article_title = title_selector.xpath('a/text()').get().strip()

            article_tags = article_selector.xpath(
                './ul[@data-type="simple:none"]/li/a/text()').getall()

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
            return article

        next_page = response.xpath(
            '//a[@class="next page-numbers"]/@href').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)