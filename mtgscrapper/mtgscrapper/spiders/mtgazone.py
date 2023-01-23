import scrapy


class MTGArenaZoneSpider(scrapy.Spider):
    name = 'mtgazone'
    start_urls = ['https://mtgazone.com/articles/']

    def parse(self, response):
        for article in response.xpath('//article'):
            print(article)