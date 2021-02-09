import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst
from datetime import datetime
from starlingbank.items import Article


class StarlingSpider(scrapy.Spider):
    name = 'starling'
    start_urls = ['https://www.starlingbank.com/blog/']

    def parse(self, response):
        articles = response.xpath('//article/a')
        for article in articles:
            category = article.xpath('.//p[@class="blog-post-preview-card__category-title"]/text()').get()
            link = article.xpath('./@href').get()
            yield response.follow(link, self.parse_find_related, cb_kwargs=dict(category=category))

    def parse_find_related(self, response, category):
        yield response.follow(response.url, self.parse_article, cb_kwargs=dict(category=category), dont_filter=True)

        articles = response.xpath('//article/article/a')
        for article in articles:
            category = article.xpath('.//p[@class="blog-post-preview-card__category-title"]/text()').get()
            link = article.xpath('./@href').get()
            yield response.follow(link, self.parse_find_related, cb_kwargs=dict(category=category))

    def parse_article(self, response, category):
        item = ItemLoader(Article())
        item.default_output_processor = TakeFirst()

        title = response.xpath('//h1[@class="blog-post__title"]/text()').get()
        if not title:
            return
        date = response.xpath('(//header[@class="blog-post__meta"]/p/text())[1]').get().strip().split()
        date[0] = date[0][:-2]
        date = " ".join(date)
        date = datetime.strptime(date, '%d %B %Y')
        date = date.strftime('%Y/%m/%d')
        content = response.xpath('//div[@class="text-content__inner"]//text()').getall()
        content = [text for text in content if text.strip()]
        content = "\n".join(content).strip()
        author = response.xpath('//a[@rel="author"]/text()').get()
        item.add_value('title', title)
        item.add_value('date', date)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('author', author)
        item.add_value('category', category)

        return item.load_item()
