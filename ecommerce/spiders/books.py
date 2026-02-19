import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    custom_settings = {
        "FEED_FORMAT": "jsonlines",
        "FEED_URI": "books.jl",
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def parse(self, response):
        books = response.css("article.product_pod")

        for book in books:
            relative_url = book.css("h3 a::attr(href)").get()
            if relative_url:
                absolute_url = response.urljoin(relative_url)
                yield scrapy.Request(absolute_url, callback=self.parse_book_details)

        next_page = response.css("li.next a::attr(href)").get()

        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_book_details(self, response):
        price_raw = response.css("p.price_color::text").get()
        price = price_raw.replace("£", "") if price_raw else "0.00"

        stock_raw = "".join(response.css("p.instock.availability::text").getall()).strip()
        amount_in_stock = stock_raw.split("(")[1].split()[0] if "(" in stock_raw else "0"

        rating_classes = response.css("p.star-rating::attr(class)").get()
        rating_text = rating_classes.replace("star-rating ", "")
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Fo ur": 4, "Five": 5}

        yield {
            "title": response.css("h1::text").get(),
            "price": float(price),
            "amount_in_stock": int(amount_in_stock),
            "rating": rating_map.get(rating_text, 0),
            "category": response.css("ul.breadcrumb li:nth-last-child(2) a::text").get(),
            "description": response.css("#product_description + p::text").get(),
            "upc": response.xpath("//th[text()='UPC']/following-sibling::td/text()").get(),
        }
