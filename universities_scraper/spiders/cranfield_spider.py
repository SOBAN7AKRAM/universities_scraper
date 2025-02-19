import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class CranfieldSpider(scrapy.Spider):
    name = "cranfield_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)  # Ensure proper superclass initialization
        self.base_url = "https://search.cranfield.ac.uk/s/search.html"
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.base_url, "?f.Tabs%7Ccranfield~ds-people=People&f.Type%7CpeopleType=Staff&num_ranks=50&query=a&collection=cranfield~sp-meta"),
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        try:
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            current_emails = regex.findall(soup.get_text())
            for email in current_emails:
                yield {"email": email, "university": "cranfield.ac.uk"}
                        
            next_page_element = next(
    (a for a in soup.find_all("a", class_="page-link") if "Next" in a.get_text(strip=True)),
    None
)
            if next_page_element:
                next_page_href = next_page_element.get("href")
                if next_page_href:
                    next_page_url = urljoin(self.base_url, next_page_href)
                    yield Request(
                        url=next_page_url,
                        callback=self.parse,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                            "playwright_context": "university-scraper",
                        },
                    )
            

        finally:
            await page.close()
