import re
from typing import Iterable, Any, Generator

import scrapy
from scrapy.http import HtmlResponse

from ecommerce.items import EcommerceItem


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    custom_settings = {
        "FEED_FORMAT": "jsonlines",
        "FEED_URI": "books.jl",
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def parse(
            self,
            response: HtmlResponse
    ) -> Iterable[scrapy.Request]:

        book_links = response.css(
            "article.product_pod h3 a::attr(href)"
        ).getall()

        for book_link in book_links:
            yield response.follow(
                book_link,
                callback=self.parse_book_details
            )

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_book_details(
            self,
            response: HtmlResponse
    ) -> Generator[EcommerceItem, Any, None]:

        item = EcommerceItem()

        item["title"] = response.css("h1::text").get()

        price_raw = response.css("p.price_color::text").get(default="0.00")
        item["price"] = float(re.sub(r"[^\d.]", "", price_raw))

        stock_raw = "".join(
            response.css("p.instock.availability::text").getall()
        )
        stock_match = re.search(r"\((\d+) available\)", stock_raw)
        item["amount_in_stock"] = (
            int(stock_match.group(1)) if stock_match else 0
        )

        rating_classes = response.css(
            "p.star-rating::attr(class)"
        ).get(default="")
        rating_text = rating_classes.replace("star-rating", "").strip()
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        item["rating"] = rating_map.get(rating_text, 0)

        item["category"] = response.css(
            "ul.breadcrumb li:nth-last-child(2) a::text"
        ).get()

        item["description"] = response.css(
            "#product_description + p::text"
        ).get(default="").strip()

        item["upc"] = response.xpath(
            "//th[text()='UPC']/following-sibling::td/text()"
        ).get()

        yield item
