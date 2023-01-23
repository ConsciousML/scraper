import scrapy


class MTGArenaZoneSpider(scrapy.Spider):
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

            yield {
                'id': article_selector.attrib['id'],
                'url': article_url,
                'title': article_title,
                'tags': article_tags,
                'author': author_name,
                'date': article_date
            }